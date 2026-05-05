from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any


def append_event(
    events: list[dict[str, Any]],
    *,
    work_item_id: str,
    agent_id: str,
    action_type: str,
    event_type: str | None = None,
    input_data: Mapping[str, Any] | None = None,
    output_data: Mapping[str, Any] | None = None,
    confidence: float = 1.0,
    human_override: bool = False,
    evidence_chunk_ids: list[str] | None = None,
) -> None:
    events.append(
        {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "work_item_id": work_item_id,
            "agent_id": agent_id,
            "event_type": event_type or _event_type_for_action(action_type),
            "action_type": action_type,
            "input": dict(input_data or {}),
            "output": dict(output_data or {}),
            "confidence": confidence,
            "human_override": human_override,
            "evidence_chunk_ids": list(evidence_chunk_ids or []),
        }
    )


def count_events(events: list[dict[str, Any]], action_type: str) -> int:
    return sum(1 for event in events if event.get("action_type") == action_type)


def _event_type_for_action(action_type: str) -> str:
    return {
        "route": "intent_classified",
        "plan": "plan_created",
        "execute_tool": "tool_executed",
        "approve": "approval_requested",
        "block": "block",
        "final_response_generated": "final_response_generated",
    }.get(action_type, action_type)
