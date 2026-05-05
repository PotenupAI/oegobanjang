from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DocumentStatus:
    document_id: str
    worker_id: str
    document_type: str
    status: str = "missing"
