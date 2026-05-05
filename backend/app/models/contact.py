from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContactMessage:
    message_id: str
    worker_id: str
    channel: str
    status: str = "draft"
