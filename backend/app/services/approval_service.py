from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL

from app.models.approval import ApprovalRecord
from app.schemas.approval import ApprovalCreate, ApprovalDecision


_APPROVALS: dict[str, ApprovalRecord] = {}
_APPROVAL_INDEX: dict[tuple[str, str], str] = {}


def create_approval(payload: ApprovalCreate) -> ApprovalRecord:
    key = (payload.request_id, payload.action_type)
    if key in _APPROVAL_INDEX:
        return _APPROVALS[_APPROVAL_INDEX[key]]

    approval_id = f"appr_{uuid5(NAMESPACE_URL, ':'.join(key)).hex}"
    record = ApprovalRecord(
        approval_id=approval_id,
        request_id=payload.request_id,
        action_type=payload.action_type,
        reason=payload.reason,
    )
    _APPROVALS[approval_id] = record
    _APPROVAL_INDEX[key] = approval_id
    return record


def get_approval(approval_id: str) -> ApprovalRecord | None:
    return _APPROVALS.get(approval_id)


def list_approvals(request_id: str | None = None) -> list[ApprovalRecord]:
    records = list(_APPROVALS.values())
    if request_id is None:
        return records
    return [record for record in records if record.request_id == request_id]


def decide_approval(approval_id: str, decision: ApprovalDecision) -> ApprovalRecord | None:
    record = _APPROVALS.get(approval_id)
    if record is None:
        return None
    record.status = decision.status
    record.decided_at = datetime.now(timezone.utc)
    return record


def reset_approval_store() -> None:
    _APPROVALS.clear()
    _APPROVAL_INDEX.clear()
