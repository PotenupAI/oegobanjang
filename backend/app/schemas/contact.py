from __future__ import annotations

from pydantic import BaseModel


class ContactMessageRead(BaseModel):
    message_id: str
    worker_id: str
    channel: str
    status: str = "draft"
