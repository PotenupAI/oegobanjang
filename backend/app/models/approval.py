from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ApprovalRecord:
    approval_id: str
    request_id: str
    action_type: str
    status: str = "PENDING"
    reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime | None = None
