from __future__ import annotations

from pydantic import BaseModel


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
