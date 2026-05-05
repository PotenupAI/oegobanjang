from __future__ import annotations

from pydantic import BaseModel


class CompanyRead(BaseModel):
    company_id: str
    name: str
    industry: str | None = None
