from __future__ import annotations

from pydantic import BaseModel


class HiringRead(BaseModel):
    hiring_id: str
    company_id: str
    requested_headcount: int
    status: str = "draft"
