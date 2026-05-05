from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HiringRequest:
    hiring_id: str
    company_id: str
    requested_headcount: int
    status: str = "draft"
