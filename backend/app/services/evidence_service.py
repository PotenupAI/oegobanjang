from __future__ import annotations

import json
from uuid import NAMESPACE_URL, uuid5

from app.agent_runtime.middleware.pii_filter import mask_payload
from app.models.evidence import EvidenceRecord
from app.schemas.evidence import EvidenceCreate


REQUIRED_EVENT_ORDER = [
    "intent_classified",
    "plan_created",
    "tool_executed",
    "approval_requested",
    "approval_completed",
    "final_response_generated",
]

_EVENTS: dict[str, EvidenceRecord] = {}
_EVENT_INDEX: dict[tuple[str, str, str, str], str] = {}


def append_evidence(payload: EvidenceCreate) -> EvidenceRecord:
    key = (payload.request_id, payload.event_type, payload.agent_id, payload.action_type)
    if key in _EVENT_INDEX:
        return _EVENTS[_EVENT_INDEX[key]]

    event_id = f"ev_{uuid5(NAMESPACE_URL, ':'.join(key)).hex}"
    record = EvidenceRecord(
        event_id=event_id,
        request_id=payload.request_id,
        event_type=payload.event_type,
        agent_id=payload.agent_id,
        action_type=payload.action_type,
        payload=mask_payload(payload.payload),
    )
    _EVENTS[event_id] = record
    _EVENT_INDEX[key] = event_id
    return record


def list_evidence(request_id: str) -> list[EvidenceRecord]:
    return [record for record in _EVENTS.values() if record.request_id == request_id]


def validate_required_order(events: list[dict[str, object]]) -> bool:
    positions: dict[str, int] = {}
    for index, event in enumerate(events):
        event_type = str(event.get("event_type") or "")
        positions.setdefault(event_type, index)

    required_positions = [positions[event_type] for event_type in REQUIRED_EVENT_ORDER if event_type in positions]
    return required_positions == sorted(required_positions)


def contains_raw_pii(payload: object) -> bool:
    serialized = json.dumps(payload, ensure_ascii=False)
    return any(token in serialized for token in ["900101-1234567", "M12345678", "010-1234-5678"])


def reset_evidence_store() -> None:
    _EVENTS.clear()
    _EVENT_INDEX.clear()
