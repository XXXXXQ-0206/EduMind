"""
PostgreSQL-backed auth and chat persistence.

Legacy SQLite/JSON data can still be imported during startup, but the runtime
database is PostgreSQL.
"""
from __future__ import annotations

import json
import secrets
import shutil
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from config import config
from infrastructure.kv_store import validate_sql_identifier
from utils.auth_contracts import ADMIN_DEFAULT_PASSWORD, ADMIN_USERNAME, AuthUser


DB_PATH = config.storage_dir / "edumind.sqlite3"
LEGACY_DB_PATH = config.storage_dir / ("page" + "lm.sqlite3")
LEGACY_SQLITE_PATHS = [DB_PATH, LEGACY_DB_PATH]
SESSION_DAYS = 14


def _ensure_brand_db_path() -> None:
    if DB_PATH.exists() or not LEGACY_DB_PATH.exists():
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LEGACY_DB_PATH, DB_PATH)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_ms(value: Any) -> int:
    if value is None:
        return 0
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp() * 1000)
    except Exception:
        return 0


def _to_iso(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value))
        except Exception:
            return str(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _to_datetime(value: Any) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _json_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        parsed = json.loads(str(value))
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


class LegacySQLiteAuthDatabase:
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


class AuthDatabase:
    def __init__(
        self,
        dsn: Optional[str] = None,
        table_prefix: str = "auth",
        connection_factory: Optional[Any] = None,
    ):
        self.dsn = dsn or config.postgres_dsn
        self.table_prefix = validate_sql_identifier(table_prefix)
        self._connection_factory = connection_factory
        self.lock = threading.Lock()
        self.users_table = self._table("users")
        self.sessions_table = self._table("sessions")
        self.chats_table = self._table("chats")
        self.messages_table = self._table("chat_messages")

    def _table(self, name: str) -> str:
        return validate_sql_identifier(f"{self.table_prefix}_{name}")

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        if self._connection_factory is not None:
            with self._connection_factory() as conn:
                yield conn
            return

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgreSQL auth storage requires the 'psycopg' package") from exc

        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        self._ensure_schema()
        self.migrate_legacy_sqlite_auth()
        self.ensure_admin_user()
        self.migrate_legacy_admin_chats()

    def _ensure_schema(self) -> None:
        with self.lock, self._connection() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.users_table} (
                    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    username text NOT NULL UNIQUE,
                    password_hash text NOT NULL,
                    password_salt text NOT NULL,
                    created_at timestamptz NOT NULL,
                    updated_at timestamptz NOT NULL
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.sessions_table} (
                    token text PRIMARY KEY,
                    user_id integer NOT NULL REFERENCES {self.users_table}(id) ON DELETE CASCADE,
                    created_at timestamptz NOT NULL,
                    expires_at timestamptz NOT NULL
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.chats_table} (
                    id text PRIMARY KEY,
                    user_id integer NOT NULL REFERENCES {self.users_table}(id) ON DELETE CASCADE,
                    title text NOT NULL,
                    scope text NOT NULL,
                    response_length text NOT NULL DEFAULT 'Short',
                    include_materials boolean NOT NULL DEFAULT false,
                    material_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
                    created_at timestamptz NOT NULL,
                    updated_at timestamptz NOT NULL
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.messages_table} (
                    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    chat_id text NOT NULL REFERENCES {self.chats_table}(id) ON DELETE CASCADE,
                    role text NOT NULL,
                    content text NOT NULL,
                    at bigint NOT NULL
                )
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS {self.chats_table}_user_updated_idx "
                f"ON {self.chats_table} (user_id, updated_at DESC)"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS {self.messages_table}_chat_id_idx "
                f"ON {self.messages_table} (chat_id, id)"
            )

    def _hash_password(self, password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
        salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
        hashed = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return hashed.hex(), salt.hex()

    def ensure_admin_user(self) -> AuthUser:
        admin = self.get_user_by_username(ADMIN_USERNAME)
        if admin:
            return admin
        try:
            return self.create_user(ADMIN_USERNAME, ADMIN_DEFAULT_PASSWORD)
        except ValueError:
            admin = self.get_user_by_username(ADMIN_USERNAME)
            if admin:
                return admin
            raise

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
        with self.lock, self._connection() as conn:
            try:
                row = conn.execute(
                    f"""
                    INSERT INTO {self.users_table} (username, password_hash, password_salt, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username, created_at
                    """,
                    (normalized, password_hash, salt, now, now),
                ).fetchone()
            except Exception as exc:
                if exc.__class__.__name__ == "UniqueViolation":
                    raise ValueError("用户名已存在") from exc
                raise
        return AuthUser(id=int(row["id"]), username=str(row["username"]), created_at=_to_iso(row["created_at"]))

    def get_user_by_username(self, username: str) -> Optional[AuthUser]:
        with self.lock, self._connection() as conn:
            row = conn.execute(
                f"SELECT id, username, created_at FROM {self.users_table} WHERE username = %s",
                (username.strip(),),
            ).fetchone()
        if not row:
            return None
        return AuthUser(id=int(row["id"]), username=str(row["username"]), created_at=_to_iso(row["created_at"]))

    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        with self.lock, self._connection() as conn:
            row = conn.execute(
                f"SELECT id, username, created_at FROM {self.users_table} WHERE id = %s",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return AuthUser(id=int(row["id"]), username=str(row["username"]), created_at=_to_iso(row["created_at"]))

    def _get_user_credentials(self, user_id: int) -> Optional[dict[str, Any]]:
        with self.lock, self._connection() as conn:
            return conn.execute(
                f"""
                SELECT id, username, password_hash, password_salt, created_at
                FROM {self.users_table}
                WHERE id = %s
                """,
                (user_id,),
            ).fetchone()

    def authenticate_user(self, username: str, password: str) -> Optional[AuthUser]:
        with self.lock, self._connection() as conn:
            row = conn.execute(
                f"""
                SELECT id, username, password_hash, password_salt, created_at
                FROM {self.users_table}
                WHERE username = %s
                """,
                (username.strip(),),
            ).fetchone()
        if not row:
            return None
        password_hash, _salt = self._hash_password(password, row["password_salt"])
        if secrets.compare_digest(password_hash, row["password_hash"]):
            return AuthUser(id=int(row["id"]), username=str(row["username"]), created_at=_to_iso(row["created_at"]))
        return None

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=SESSION_DAYS)
        with self.lock, self._connection() as conn:
            conn.execute(f"DELETE FROM {self.sessions_table} WHERE user_id = %s", (user_id,))
            conn.execute(
                f"""
                INSERT INTO {self.sessions_table} (token, user_id, created_at, expires_at)
                VALUES (%s, %s, %s, %s)
                """,
                (token, user_id, now, expires),
            )
        return token

    def get_user_by_token(self, token: str) -> Optional[AuthUser]:
        if not token:
            return None
        with self.lock, self._connection() as conn:
            row = conn.execute(
                f"""
                SELECT s.expires_at, u.id, u.username, u.created_at
                FROM {self.sessions_table} s
                JOIN {self.users_table} u ON u.id = s.user_id
                WHERE s.token = %s
                """,
                (token,),
            ).fetchone()
        if not row:
            return None
        try:
            expires_at = _to_datetime(row["expires_at"])
        except Exception:
            expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        if expires_at <= datetime.now(timezone.utc):
            self.delete_session(token)
            return None
        return AuthUser(id=int(row["id"]), username=str(row["username"]), created_at=_to_iso(row["created_at"]))

    def delete_session(self, token: str) -> None:
        if not token:
            return
        with self.lock, self._connection() as conn:
            conn.execute(f"DELETE FROM {self.sessions_table} WHERE token = %s", (token,))

    def delete_sessions_for_user(self, user_id: int) -> None:
        with self.lock, self._connection() as conn:
            conn.execute(f"DELETE FROM {self.sessions_table} WHERE user_id = %s", (user_id,))

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
        with self.lock, self._connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.users_table}
                SET password_hash = %s, password_salt = %s, updated_at = %s
                WHERE id = %s
                """,
                (new_hash, new_salt, utcnow_iso(), user_id),
            )
            conn.execute(f"DELETE FROM {self.sessions_table} WHERE user_id = %s", (user_id,))

    def delete_user(self, user_id: int, password: str) -> None:
        row = self._get_user_credentials(user_id)
        if not row:
            raise ValueError("用户不存在")
        if row["username"] == ADMIN_USERNAME:
            raise ValueError("默认管理员账户不可注销")
        password_hash, _salt = self._hash_password(password, row["password_salt"])
        if not secrets.compare_digest(password_hash, row["password_hash"]):
            raise ValueError("密码不正确")
        with self.lock, self._connection() as conn:
            conn.execute(f"DELETE FROM {self.users_table} WHERE id = %s", (user_id,))

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
        with self.lock, self._connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.chats_table} (
                    id, user_id, title, scope, response_length, include_materials,
                    material_ids, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    chat_id,
                    user_id,
                    (title or "未命名对话")[:100],
                    normalized_scope,
                    response_length or "Short",
                    bool(include_materials),
                    self._jsonb(material_ids or []),
                    created,
                    updated,
                ),
            )
        return self.get_chat(user_id, chat_id)  # type: ignore[return-value]

    def update_chat_settings(
        self,
        user_id: int,
        chat_id: str,
        response_length: str,
        include_materials: bool,
        material_ids: Optional[List[str]] = None,
    ) -> None:
        with self.lock, self._connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.chats_table}
                SET response_length = %s, include_materials = %s, material_ids = %s, updated_at = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    response_length or "Short",
                    bool(include_materials),
                    self._jsonb(material_ids or []),
                    utcnow_iso(),
                    chat_id,
                    user_id,
                ),
            )

    def touch_chat(self, user_id: int, chat_id: str) -> None:
        with self.lock, self._connection() as conn:
            conn.execute(
                f"UPDATE {self.chats_table} SET updated_at = %s WHERE id = %s AND user_id = %s",
                (utcnow_iso(), chat_id, user_id),
            )

    def set_chat_updated_at(self, user_id: int, chat_id: str, updated_at: str) -> None:
        with self.lock, self._connection() as conn:
            conn.execute(
                f"UPDATE {self.chats_table} SET updated_at = %s WHERE id = %s AND user_id = %s",
                (updated_at, chat_id, user_id),
            )

    def get_chat(self, user_id: int, chat_id: str) -> Optional[Dict[str, Any]]:
        with self.lock, self._connection() as conn:
            row = conn.execute(
                f"""
                SELECT id, title, scope, response_length, include_materials, material_ids, created_at, updated_at
                FROM {self.chats_table}
                WHERE id = %s AND user_id = %s
                """,
                (chat_id, user_id),
            ).fetchone()
        if not row:
            return None
        created = _to_iso(row["created_at"])
        updated = _to_iso(row["updated_at"])
        return {
            "id": row["id"],
            "title": row["title"],
            "scope": row["scope"],
            "length": row["response_length"],
            "includeMaterials": bool(row["include_materials"]),
            "materialIds": _json_list(row["material_ids"]),
            "createdAt": _to_ms(created),
            "updatedAt": _to_ms(updated),
            "created_at": created,
            "updated_at": updated,
            "at": _to_ms(updated or created),
        }

    def list_chats(self, user_id: int, query: Optional[str] = None, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = f"""
            SELECT id, title, scope, created_at, updated_at
            FROM {self.chats_table}
            WHERE user_id = %s
        """
        params: List[Any] = [user_id]
        if scope in ("student", "teacher"):
            sql += " AND scope = %s"
            params.append(scope)
        if query and query.strip():
            sql += " AND lower(title) LIKE %s"
            params.append(f"%{query.strip().lower()}%")
        sql += " ORDER BY updated_at DESC"

        with self.lock, self._connection() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "scope": row["scope"],
                "createdAt": _to_ms(row["created_at"]),
                "updatedAt": _to_ms(row["updated_at"]),
                "created_at": _to_iso(row["created_at"]),
                "updated_at": _to_iso(row["updated_at"]),
                "at": _to_ms(row["updated_at"] or row["created_at"]),
            }
            for row in rows
        ]

    def add_message(self, user_id: int, chat_id: str, role: str, content: str, at: Optional[int] = None) -> None:
        if not self.get_chat(user_id, chat_id):
            raise ValueError("chat not found")
        at_ms = at if at is not None else int(datetime.now(timezone.utc).timestamp() * 1000)
        with self.lock, self._connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.messages_table} (chat_id, role, content, at)
                VALUES (%s, %s, %s, %s)
                """,
                (chat_id, role, content, at_ms),
            )
            conn.execute(
                f"UPDATE {self.chats_table} SET updated_at = %s WHERE id = %s AND user_id = %s",
                (utcnow_iso(), chat_id, user_id),
            )

    def get_messages(self, user_id: int, chat_id: str) -> List[Dict[str, Any]]:
        if not self.get_chat(user_id, chat_id):
            return []
        with self.lock, self._connection() as conn:
            rows = conn.execute(
                f"""
                SELECT role, content, at
                FROM {self.messages_table}
                WHERE chat_id = %s
                ORDER BY id ASC
                """,
                (chat_id,),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"], "at": int(row["at"])} for row in rows]

    def delete_chat(self, user_id: int, chat_id: str) -> None:
        with self.lock, self._connection() as conn:
            conn.execute(f"DELETE FROM {self.chats_table} WHERE id = %s AND user_id = %s", (chat_id, user_id))

    def migrate_legacy_sqlite_auth(self) -> None:
        for path in LEGACY_SQLITE_PATHS:
            if path.exists():
                try:
                    self._migrate_legacy_sqlite_path(path)
                except Exception as exc:
                    print(f"[WARN] failed to migrate legacy SQLite auth store {path}: {exc}")
                return

    def _migrate_legacy_sqlite_path(self, path: Path) -> None:
        sqlite_conn = sqlite3.connect(path)
        sqlite_conn.row_factory = sqlite3.Row
        try:
            if not self._sqlite_has_table(sqlite_conn, "users"):
                return
            with self.lock, self._connection() as conn:
                for row in sqlite_conn.execute("SELECT id, username, password_hash, password_salt, created_at, updated_at FROM users"):
                    conn.execute(
                        f"""
                        INSERT INTO {self.users_table} (id, username, password_hash, password_salt, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (row["id"], row["username"], row["password_hash"], row["password_salt"], row["created_at"], row["updated_at"]),
                    )
                if self._sqlite_has_table(sqlite_conn, "sessions"):
                    for row in sqlite_conn.execute("SELECT token, user_id, created_at, expires_at FROM sessions"):
                        conn.execute(
                            f"""
                            INSERT INTO {self.sessions_table} (token, user_id, created_at, expires_at)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (row["token"], row["user_id"], row["created_at"], row["expires_at"]),
                        )
                if self._sqlite_has_table(sqlite_conn, "chats"):
                    for row in sqlite_conn.execute(
                        """
                        SELECT id, user_id, title, scope, response_length, include_materials,
                               material_ids_json, created_at, updated_at
                        FROM chats
                        """
                    ):
                        conn.execute(
                            f"""
                            INSERT INTO {self.chats_table} (
                                id, user_id, title, scope, response_length, include_materials,
                                material_ids, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (
                                row["id"],
                                row["user_id"],
                                row["title"],
                                row["scope"],
                                row["response_length"],
                                bool(row["include_materials"]),
                                self._jsonb(_json_list(row["material_ids_json"])),
                                row["created_at"],
                                row["updated_at"],
                            ),
                        )
                if self._sqlite_has_table(sqlite_conn, "chat_messages"):
                    for row in sqlite_conn.execute(
                        """
                        SELECT m.id, m.chat_id, m.role, m.content, m.at
                        FROM chat_messages m
                        JOIN chats c ON c.id = m.chat_id
                        """
                    ):
                        conn.execute(
                            f"""
                            INSERT INTO {self.messages_table} (id, chat_id, role, content, at)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (row["id"], row["chat_id"], row["role"], row["content"], row["at"]),
                        )
                self._refresh_identity_sequence(conn, self.users_table)
                self._refresh_identity_sequence(conn, self.messages_table)
        finally:
            sqlite_conn.close()

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
            if not chat_id or self.get_chat(admin.id, chat_id):
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
                    self.set_chat_updated_at(admin.id, chat_id, str(data.get("updated_at") or data.get("created_at")))
            except Exception:
                continue

    def _jsonb(self, value: Any) -> Any:
        if self._connection_factory is not None:
            return value
        from psycopg.types.json import Jsonb

        return Jsonb(value)

    def _refresh_identity_sequence(self, conn: Any, table_name: str) -> None:
        conn.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence(%s, 'id'),
                GREATEST(COALESCE((SELECT MAX(id) FROM {table_name}), 1), 1),
                true
            )
            """,
            (table_name,),
        )

    def _sqlite_has_table(self, conn: sqlite3.Connection, table_name: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None


auth_db = AuthDatabase()
