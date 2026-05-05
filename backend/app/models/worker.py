from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Worker:
    worker_id: str
    company_id: str
    name: str
    visa_type: str | None = None
