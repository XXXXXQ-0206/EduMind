"""
SQLite-backed auth and chat persistence.
"""
from __future__ import annotations

import json
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import config


DB_PATH = config.storage_dir / "pagelm.sqlite3"
SESSION_DAYS = 14
ADMIN_USERNAME = "admin1"
ADMIN_DEFAULT_PASSWORD = "admin123"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_ms(value: Optional[str]) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value).timestamp() * 1000)
    except Exception:
        return 0


@dataclass
class AuthUser:
    id: int
    username: str
    created_at: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "createdAt": self.created_at,
        }


class AuthDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.lock, self._connect() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    response_length TEXT NOT NULL DEFAULT 'Short',
                    include_materials INTEGER NOT NULL DEFAULT 0,
                    material_ids_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    at INTEGER NOT NULL,
                    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                );
                """
            )
            conn.commit()

        self.ensure_admin_user()
        self.migrate_legacy_admin_chats()

    def _hash_password(self, password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
        salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
        hashed = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return hashed.hex(), salt.hex()

    def ensure_admin_user(self) -> AuthUser:
        admin = self.get_user_by_username(ADMIN_USERNAME)
        if admin:
            return admin
        return self.create_user(ADMIN_USERNAME, ADMIN_DEFAULT_PASSWORD)

    def create_user(self, username: str, password: str) -> AuthUser:
        normalized = username.strip()
        if not normalized:
            raise ValueError("用户名不能为空")
        if len(normalized) < 2:
            raise ValueError("用户名至少 2 个字符")
        if len(password) < 6:
            raise ValueError("密码至少 6 位")

        password_hash, salt = self._hash_password(password)
        now = utcnow_iso()
        with self.lock, self._connect() as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, password_salt, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (normalized, password_hash, salt, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("用户名已存在") from exc
            conn.commit()
            user_id = int(cur.lastrowid)
        return AuthUser(id=user_id, username=normalized, created_at=now)

    def get_user_by_username(self, username: str) -> Optional[AuthUser]:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, created_at FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
        if not row:
            return None
        return AuthUser(id=int(row["id"]), username=row["username"], created_at=row["created_at"])

    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return AuthUser(id=int(row["id"]), username=row["username"], created_at=row["created_at"])

    def _get_user_credentials(self, user_id: int) -> Optional[sqlite3.Row]:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, password_hash, password_salt, created_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        return row

    def authenticate_user(self, username: str, password: str) -> Optional[AuthUser]:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, password_hash, password_salt, created_at
                FROM users
                WHERE username = ?
                """,
                (username.strip(),),
            ).fetchone()
        if not row:
            return None
        password_hash, _salt = self._hash_password(password, row["password_salt"])
        if secrets.compare_digest(password_hash, row["password_hash"]):
            return AuthUser(id=int(row["id"]), username=row["username"], created_at=row["created_at"])
        return None

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=SESSION_DAYS)
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.execute(
                """
                INSERT INTO sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (token, user_id, now.isoformat(), expires.isoformat()),
            )
            conn.commit()
        return token

    def get_user_by_token(self, token: str) -> Optional[AuthUser]:
        if not token:
            return None
        with self.lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT s.expires_at, u.id, u.username, u.created_at
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = ?
                """,
                (token,),
            ).fetchone()
        if not row:
            return None
        try:
            expires_at = datetime.fromisoformat(row["expires_at"])
        except Exception:
            expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        if expires_at <= datetime.now(timezone.utc):
            self.delete_session(token)
            return None
        return AuthUser(id=int(row["id"]), username=row["username"], created_at=row["created_at"])

    def delete_session(self, token: str) -> None:
        if not token:
            return
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

    def delete_sessions_for_user(self, user_id: int) -> None:
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.commit()

    def verify_user_password(self, user_id: int, password: str) -> bool:
        row = self._get_user_credentials(user_id)
        if not row:
            return False
        password_hash, _salt = self._hash_password(password, row["password_salt"])
        return secrets.compare_digest(password_hash, row["password_hash"])

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        row = self._get_user_credentials(user_id)
        if not row:
            raise ValueError("用户不存在")
        if len(new_password) < 6:
            raise ValueError("新密码至少 6 位")
        old_hash, _old_salt = self._hash_password(old_password, row["password_salt"])
        if not secrets.compare_digest(old_hash, row["password_hash"]):
            raise ValueError("旧密码不正确")
        new_hash, new_salt = self._hash_password(new_password)
        now = utcnow_iso()
        with self.lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET password_hash = ?, password_salt = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_hash, new_salt, now, user_id),
            )
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.commit()

    def delete_user(self, user_id: int, password: str) -> None:
        row = self._get_user_credentials(user_id)
        if not row:
            raise ValueError("用户不存在")
        if row["username"] == ADMIN_USERNAME:
            raise ValueError("默认管理员账户不可注销")
        password_hash, _salt = self._hash_password(password, row["password_salt"])
        if not secrets.compare_digest(password_hash, row["password_hash"]):
            raise ValueError("密码不正确")
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

    def create_chat(
        self,
        user_id: int,
        title: str,
        scope: str,
        response_length: str = "Short",
        include_materials: bool = False,
        material_ids: Optional[List[str]] = None,
        chat_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_scope = scope if scope in ("student", "teacher") else "student"
        now = utcnow_iso()
        chat_id = chat_id or str(uuid.uuid4())
        created = created_at or now
        updated = updated_at or created
        with self.lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chats (
                    id, user_id, title, scope, response_length, include_materials,
                    material_ids_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    user_id,
                    (title or "未命名对话")[:100],
                    normalized_scope,
                    response_length or "Short",
                    1 if include_materials else 0,
                    json.dumps(material_ids or [], ensure_ascii=False),
                    created,
                    updated,
                ),
            )
            conn.commit()
        return self.get_chat(user_id, chat_id)  # type: ignore[return-value]

    def update_chat_settings(
        self,
        user_id: int,
        chat_id: str,
        response_length: str,
        include_materials: bool,
        material_ids: Optional[List[str]] = None,
    ) -> None:
        now = utcnow_iso()
        with self.lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE chats
                SET response_length = ?, include_materials = ?, material_ids_json = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    response_length or "Short",
                    1 if include_materials else 0,
                    json.dumps(material_ids or [], ensure_ascii=False),
                    now,
                    chat_id,
                    user_id,
                ),
            )
            conn.commit()

    def touch_chat(self, user_id: int, chat_id: str) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ? AND user_id = ?",
                (utcnow_iso(), chat_id, user_id),
            )
            conn.commit()

    def set_chat_updated_at(self, user_id: int, chat_id: str, updated_at: str) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ? AND user_id = ?",
                (updated_at, chat_id, user_id),
            )
            conn.commit()

    def get_chat(self, user_id: int, chat_id: str) -> Optional[Dict[str, Any]]:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, title, scope, response_length, include_materials, material_ids_json, created_at, updated_at
                FROM chats
                WHERE id = ? AND user_id = ?
                """,
                (chat_id, user_id),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "scope": row["scope"],
            "length": row["response_length"],
            "includeMaterials": bool(row["include_materials"]),
            "materialIds": json.loads(row["material_ids_json"] or "[]"),
            "createdAt": _to_ms(row["created_at"]),
            "updatedAt": _to_ms(row["updated_at"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "at": _to_ms(row["updated_at"] or row["created_at"]),
        }

    def list_chats(self, user_id: int, query: Optional[str] = None, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = """
            SELECT id, title, scope, created_at, updated_at
            FROM chats
            WHERE user_id = ?
        """
        params: List[Any] = [user_id]
        if scope in ("student", "teacher"):
            sql += " AND scope = ?"
            params.append(scope)
        if query and query.strip():
            sql += " AND lower(title) LIKE ?"
            params.append(f"%{query.strip().lower()}%")
        sql += " ORDER BY updated_at DESC"

        with self.lock, self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "scope": row["scope"],
                "createdAt": _to_ms(row["created_at"]),
                "updatedAt": _to_ms(row["updated_at"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "at": _to_ms(row["updated_at"] or row["created_at"]),
            }
            for row in rows
        ]

    def add_message(self, user_id: int, chat_id: str, role: str, content: str, at: Optional[int] = None) -> None:
        if not self.get_chat(user_id, chat_id):
            raise ValueError("chat not found")
        at_ms = at if at is not None else int(datetime.now(timezone.utc).timestamp() * 1000)
        with self.lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (chat_id, role, content, at)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, role, content, at_ms),
            )
            conn.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ? AND user_id = ?",
                (utcnow_iso(), chat_id, user_id),
            )
            conn.commit()

    def get_messages(self, user_id: int, chat_id: str) -> List[Dict[str, Any]]:
        if not self.get_chat(user_id, chat_id):
            return []
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, at
                FROM chat_messages
                WHERE chat_id = ?
                ORDER BY id ASC
                """,
                (chat_id,),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"], "at": int(row["at"])} for row in rows]

    def delete_chat(self, user_id: int, chat_id: str) -> None:
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))
            conn.commit()

    def migrate_legacy_admin_chats(self) -> None:
        admin = self.ensure_admin_user()
        base = config.storage_dir
        for path in base.glob("chat_*.json"):
            name = path.name
            if name.endswith("_messages.json") or name.endswith("_length.json") or name.endswith("_materials.json"):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            chat_id = str(data.get("id") or "")
            if not chat_id:
                continue
            if self.get_chat(admin.id, chat_id):
                continue

            scope = str(data.get("scope") or "student").strip().lower()
            if scope not in ("student", "teacher"):
                scope = "student"
            length_path = base / f"chat_{chat_id}_length.json"
            materials_path = base / f"chat_{chat_id}_materials.json"
            messages_path = base / f"chat_{chat_id}_messages.json"

            try:
                response_length = json.loads(length_path.read_text(encoding="utf-8")) if length_path.exists() else "Short"
            except Exception:
                response_length = "Short"
            try:
                materials_cfg = json.loads(materials_path.read_text(encoding="utf-8")) if materials_path.exists() else {}
            except Exception:
                materials_cfg = {}
            try:
                messages = json.loads(messages_path.read_text(encoding="utf-8")) if messages_path.exists() else []
            except Exception:
                messages = []

            try:
                self.create_chat(
                    user_id=admin.id,
                    title=str(data.get("title") or "未命名对话"),
                    scope=scope,
                    response_length=str(response_length or "Short"),
                    include_materials=bool((materials_cfg or {}).get("include")),
                    material_ids=(materials_cfg or {}).get("ids") or [],
                    chat_id=chat_id,
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at") or data.get("created_at"),
                )
                for item in messages if isinstance(messages, list) else []:
                    if not isinstance(item, dict):
                        continue
                    self.add_message(
                        admin.id,
                        chat_id,
                        str(item.get("role") or "user"),
                        str(item.get("content") or ""),
                        int(item.get("at") or 0) or None,
                    )
                if data.get("updated_at") or data.get("created_at"):
                    self.set_chat_updated_at(
                        admin.id,
                        chat_id,
                        str(data.get("updated_at") or data.get("created_at")),
                    )
            except Exception:
                continue


auth_db = AuthDatabase(DB_PATH)
