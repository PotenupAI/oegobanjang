from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Company:
    company_id: str
    name: str
    industry: str | None = None
