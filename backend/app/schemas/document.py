from __future__ import annotations

from pydantic import BaseModel


class DocumentRead(BaseModel):
    document_id: str
    worker_id: str
    document_type: str
    status: str = "missing"
