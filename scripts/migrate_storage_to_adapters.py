"""Migrate legacy local storage into the configured KV and ObjectStore adapters.

The command is intentionally dry-run by default. Pass ``--write`` to copy data
into the providers selected by KV_STORE_PROVIDER and OBJECT_STORE_PROVIDER.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from config import config
from infrastructure.kv_store import JsonFileKeyValueStore, KeyValueStore, create_kv_store
from infrastructure.object_store import ObjectStore, create_object_store, normalize_object_key
from utils.storage import VectorStore


EXACT_KV_KEYS = {
    "debates_index": "debates:index",
    "flashcards": "flashcards",
    "flashcard_decks": "flashcard_decks",
    "files": "files",
    "files_teacher": "files_teacher",
    "speaking_history": "speaking:history",
}

ENTITY_SUFFIXES: dict[str, tuple[str, ...]] = {
    "chat": ("messages", "length", "materials", "settings"),
    "quiz": ("topic", "count", "difficulty", "materials", "quiz", "attempts"),
    "note": ("payload", "notes"),
    "podcast": ("payload", "script"),
    "lesson_plan": ("topic", "materials", "plan"),
    "paper": ("topic", "materials", "difficulty", "counts", "paper", "run_state"),
    "video": (
        "topic",
        "materials",
        "script",
        "video_url",
        "local_path",
        "audio_path",
        "video_error",
        "phase",
        "run_state",
        "video_source",
        "video_provider",
        "video_task_id",
        "video_request_id",
    ),
    "slide": ("slides",),
    "exam_run": ("questions", "run_state"),
    "debate": ("analysis",),
    "flashcard_deck": (),
    "flashcard": (),
}

SPECIAL_PREFIX_KEYS = (
    ("files_teacher_user_", "files_teacher:user:{}"),
    ("files_user_", "files:user:{}"),
    ("planner_tasks_user_", "planner:tasks:user:{}"),
)

OBJECT_DIRS = {
    "uploads",
    "smartnotes",
    "podcasts",
    "speaking",
    "slides",
    "teaching_videos",
    "lesson_plans",
    "papers",
    "flashcards",
}

EXCLUDED_OBJECT_DIRS = {".object-cache", ".tmp", "__pycache__", "cache", "json"}


@dataclass
class MigrationReport:
    dry_run: bool
    source_dir: str
    kv_scanned: int = 0
    kv_written: int = 0
    kv_skipped: int = 0
    kv_failed: int = 0
    vectors_scanned: int = 0
    vectors_written: int = 0
    vectors_skipped: int = 0
    vectors_failed: int = 0
    objects_scanned: int = 0
    objects_written: int = 0
    objects_skipped: int = 0
    objects_failed: int = 0
    errors: list[str] = field(default_factory=list)


def restore_legacy_kv_key(stem: str) -> str:
    """Restore an EduMind KV key from its legacy sanitized JSON filename stem."""

    if stem in EXACT_KV_KEYS:
        return EXACT_KV_KEYS[stem]

    for prefix, template in SPECIAL_PREFIX_KEYS:
        if stem.startswith(prefix):
            entity_id = stem[len(prefix):]
            return template.format(entity_id)

    for prefix in sorted(ENTITY_SUFFIXES, key=len, reverse=True):
        marker = f"{prefix}_"
        if not stem.startswith(marker):
            continue
        remainder = stem[len(marker):]
        for suffix in sorted(ENTITY_SUFFIXES[prefix], key=len, reverse=True):
            suffix_marker = f"_{suffix}"
            if remainder.endswith(suffix_marker):
                entity_id = remainder[: -len(suffix_marker)]
                return f"{prefix}:{entity_id}:{suffix}"
        return f"{prefix}:{remainder}"

    return stem


def iter_legacy_kv_files(source_dir: Path) -> Iterable[tuple[str, Path]]:
    for file_path in sorted(source_dir.glob("*.json")):
        if not file_path.is_file():
            continue
        if file_path.stem.startswith("vectors_"):
            continue
        yield restore_legacy_kv_key(file_path.stem), file_path


def iter_legacy_vector_files(source_dir: Path) -> Iterable[tuple[str, Path]]:
    for file_path in sorted(source_dir.glob("vectors_*.json")):
        if not file_path.is_file():
            continue
        yield file_path.stem.removeprefix("vectors_"), file_path


def iter_legacy_object_files(source_dir: Path, object_dirs: Optional[set[str]] = None) -> Iterable[tuple[str, Path]]:
    selected_dirs = object_dirs or OBJECT_DIRS
    for directory_name in sorted(selected_dirs):
        if directory_name in EXCLUDED_OBJECT_DIRS:
            continue
        root = source_dir / directory_name
        if not root.exists() or not root.is_dir():
            continue
        for file_path in sorted(root.rglob("*")):
            if not file_path.is_file():
                continue
            if any(part in EXCLUDED_OBJECT_DIRS for part in file_path.relative_to(source_dir).parts):
                continue
            key = normalize_object_key(file_path.relative_to(source_dir).as_posix())
            if key:
                yield key, file_path


async def migrate_kv(
    source_dir: Path,
    target: KeyValueStore,
    report: MigrationReport,
    *,
    write: bool,
) -> None:
    source = JsonFileKeyValueStore(base_dir=source_dir)
    for key, file_path in iter_legacy_kv_files(source_dir):
        report.kv_scanned += 1
        try:
            value = await source.get(file_path.stem)
            if value is None:
                report.kv_skipped += 1
                continue
            if write:
                await target.set(key, value)
                report.kv_written += 1
            else:
                report.kv_skipped += 1
        except Exception as exc:
            report.kv_failed += 1
            report.errors.append(f"kv:{file_path.name}:{type(exc).__name__}:{exc}")


async def migrate_objects(
    source_dir: Path,
    target: ObjectStore,
    report: MigrationReport,
    *,
    write: bool,
) -> None:
    for key, file_path in iter_legacy_object_files(source_dir):
        report.objects_scanned += 1
        try:
            if write:
                await target.put_file(key, file_path)
                report.objects_written += 1
            else:
                report.objects_skipped += 1
        except Exception as exc:
            report.objects_failed += 1
            report.errors.append(f"object:{key}:{type(exc).__name__}:{exc}")


async def migrate_vectors(
    source_dir: Path,
    report: MigrationReport,
    *,
    write: bool,
) -> None:
    source = JsonFileKeyValueStore(base_dir=source_dir)
    for namespace, file_path in iter_legacy_vector_files(source_dir):
        report.vectors_scanned += 1
        try:
            value = await source.get(file_path.stem)
            if not isinstance(value, dict):
                report.vectors_skipped += 1
                continue
            texts = value.get("texts")
            vectors = value.get("vectors")
            metadatas = value.get("metadatas")
            if not isinstance(texts, list) or not isinstance(vectors, list):
                report.vectors_skipped += 1
                continue
            if write:
                await VectorStore(namespace).add_precomputed_documents(texts, vectors, metadatas if isinstance(metadatas, list) else None)
                report.vectors_written += 1
            else:
                report.vectors_skipped += 1
        except Exception as exc:
            report.vectors_failed += 1
            report.errors.append(f"vector:{file_path.name}:{type(exc).__name__}:{exc}")


async def run_migration(
    source_dir: Path,
    *,
    write: bool,
    include_kv: bool,
    include_objects: bool,
    include_vectors: bool = True,
) -> MigrationReport:
    source_dir = source_dir.resolve()
    if not source_dir.exists() or not source_dir.is_dir():
        raise FileNotFoundError(f"source storage directory not found: {source_dir}")

    report = MigrationReport(dry_run=not write, source_dir=str(source_dir))
    if include_kv:
        await migrate_kv(source_dir, create_kv_store(), report, write=write)
    if include_vectors:
        await migrate_vectors(source_dir, report, write=write)
    if include_objects:
        await migrate_objects(source_dir, create_object_store(), report, write=write)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=config.storage_dir, help="Legacy storage directory")
    parser.add_argument("--write", action="store_true", help="Actually write into configured adapters")
    parser.add_argument("--skip-kv", action="store_true", help="Skip JSON/KV migration")
    parser.add_argument("--skip-vectors", action="store_true", help="Skip legacy vector JSON migration")
    parser.add_argument("--skip-objects", action="store_true", help="Skip object/artifact migration")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    report = await run_migration(
        args.source_dir,
        write=bool(args.write),
        include_kv=not args.skip_kv,
        include_vectors=not args.skip_vectors,
        include_objects=not args.skip_objects,
    )
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
