from __future__ import annotations

from pydantic import BaseModel


class WorkerRead(BaseModel):
    worker_id: str
    company_id: str
    name: str
    visa_type: str | None = None
