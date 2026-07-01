"""Object storage adapters.

The local adapter keeps the current filesystem behavior. The interface mirrors
what the services need from S3/MinIO later: store bytes, delete objects, resolve
URLs, and resolve local paths while legacy parsers still need filesystem access.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, Protocol

import aiofiles

from config import config


class ObjectStore(Protocol):
    async def put_bytes(self, key: str, content: bytes) -> str:
        ...

    async def put_file(self, key: str, source_path: Path) -> str:
        ...

    async def get_bytes(self, key: str) -> bytes:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def delete_prefix(self, prefix: str) -> None:
        ...

    def url_for(self, key: str) -> str:
        ...

    def path_for(self, key: str) -> Path:
        ...


class LocalObjectStore:
    """Filesystem-backed object store rooted at ``config.storage_dir``."""

    def __init__(self, base_dir: Optional[Path] = None, public_base_url: Optional[str] = None):
        self.base_dir = base_dir or config.storage_dir
        self.public_base_url = (public_base_url or config.object_store_base_url or "/storage").rstrip("/")

    async def put_bytes(self, key: str, content: bytes) -> str:
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as file:
            await file.write(content)
        return self.url_for(key)

    async def put_file(self, key: str, source_path: Path) -> str:
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() == path.resolve():
            return self.url_for(key)
        async with aiofiles.open(source_path, "rb") as source:
            async with aiofiles.open(path, "wb") as target:
                while True:
                    chunk = await source.read(1024 * 1024)
                    if not chunk:
                        break
                    await target.write(chunk)
        return self.url_for(key)

    async def get_bytes(self, key: str) -> bytes:
        async with aiofiles.open(self.path_for(key), "rb") as file:
            return await file.read()

    async def delete(self, key: str) -> None:
        path = self.path_for(key)
        if path.exists():
            path.unlink()

    async def delete_prefix(self, prefix: str) -> None:
        normalized = normalize_object_key(prefix).rstrip("/")
        if not normalized:
            raise ValueError("Refusing to delete the object-store root")

        base = self.base_dir.resolve()
        root = self.path_for(normalized).resolve()
        if base != root and base not in root.parents:
            raise ValueError(f"Object key escapes storage root: {prefix}")
        if not root.exists():
            return
        if root.is_file():
            root.unlink()
            return

        for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        root.rmdir()

    def url_for(self, key: str) -> str:
        return f"{self.public_base_url}/{normalize_object_key(key)}"

    def path_for(self, key: str) -> Path:
        return self.base_dir / normalize_object_key(key)


class S3ObjectStore:
    """S3/MinIO-compatible object store."""

    def __init__(self, public_base_url: Optional[str] = None):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("OBJECT_STORE_PROVIDER=s3 requires the 'boto3' package") from exc

        if not config.s3_bucket:
            raise ValueError("S3_BUCKET is required when OBJECT_STORE_PROVIDER=s3")

        self.bucket = config.s3_bucket
        self.public_base_url = (public_base_url or config.object_store_base_url or "").rstrip("/")
        self.cache_dir = (config.s3_cache_dir or (config.storage_dir / ".object-cache")).resolve()
        self.client = boto3.client(
            "s3",
            endpoint_url=config.s3_endpoint_url,
            region_name=config.s3_region,
            aws_access_key_id=config.s3_access_key_id,
            aws_secret_access_key=config.s3_secret_access_key,
        )

    async def put_bytes(self, key: str, content: bytes) -> str:
        normalized = normalize_object_key(key)
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=normalized,
            Body=content,
        )
        return self.url_for(normalized)

    async def put_file(self, key: str, source_path: Path) -> str:
        normalized = normalize_object_key(key)
        await asyncio.to_thread(self.client.upload_file, str(source_path), self.bucket, normalized)
        return self.url_for(normalized)

    async def get_bytes(self, key: str) -> bytes:
        normalized = normalize_object_key(key)

        def _get() -> bytes:
            response = self.client.get_object(Bucket=self.bucket, Key=normalized)
            return response["Body"].read()

        return await asyncio.to_thread(_get)

    async def delete(self, key: str) -> None:
        normalized = normalize_object_key(key)
        if normalized:
            await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=normalized)

    async def delete_prefix(self, prefix: str) -> None:
        normalized = normalize_object_key(prefix).rstrip("/")
        if not normalized:
            raise ValueError("Refusing to delete the object-store root")

        def _delete_prefix() -> None:
            token: Optional[str] = None
            while True:
                kwargs = {"Bucket": self.bucket, "Prefix": normalized}
                if token:
                    kwargs["ContinuationToken"] = token
                response = self.client.list_objects_v2(**kwargs)
                objects = [{"Key": item["Key"]} for item in response.get("Contents", [])]
                if objects:
                    self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects})
                if not response.get("IsTruncated"):
                    break
                token = response.get("NextContinuationToken")

        await asyncio.to_thread(_delete_prefix)

    def url_for(self, key: str) -> str:
        normalized = normalize_object_key(key)
        if self.public_base_url:
            return f"{self.public_base_url}/{normalized}"
        if config.s3_endpoint_url:
            return f"{config.s3_endpoint_url.rstrip('/')}/{self.bucket}/{normalized}"
        return f"https://{self.bucket}.s3.{config.s3_region}.amazonaws.com/{normalized}"

    def path_for(self, key: str) -> Path:
        normalized = normalize_object_key(key)
        path = (self.cache_dir / normalized).resolve()
        if self.cache_dir != path and self.cache_dir not in path.parents:
            raise ValueError(f"Object key escapes cache root: {key}")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            self.client.download_file(self.bucket, normalized, str(path))
        return path


def normalize_object_key(key: str) -> str:
    return str(key or "").strip().replace("\\", "/").lstrip("/")


def create_object_store(base_dir: Optional[Path] = None) -> ObjectStore:
    provider = (config.object_store_provider or "local").strip().lower()
    if provider == "local":
        return LocalObjectStore(base_dir=base_dir)
    if provider in {"s3", "minio"}:
        return S3ObjectStore()
    raise ValueError(f"Unsupported OBJECT_STORE_PROVIDER: {provider}")
