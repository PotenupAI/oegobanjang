from __future__ import annotations

from pydantic import BaseModel


class VisaRead(BaseModel):
    visa_id: str
    worker_id: str
    visa_type: str
    expiry_date: str | None = None
