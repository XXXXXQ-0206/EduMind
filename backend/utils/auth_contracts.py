"""Side-effect-free authentication contracts shared across services."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


ADMIN_USERNAME = "admin1"
ADMIN_DEFAULT_PASSWORD = "admin123"


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
