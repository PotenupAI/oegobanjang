from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    user_id: str
    email: str
    role: str = "manager"
