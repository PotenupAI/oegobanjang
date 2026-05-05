from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VisaStatus:
    visa_id: str
    worker_id: str
    visa_type: str
    expiry_date: str | None = None
