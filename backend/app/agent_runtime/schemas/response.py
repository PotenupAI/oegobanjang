from __future__ import annotations

from typing import Any, TypedDict


class WorkflowResponse(TypedDict, total=False):
    status: str
    case_type: str
    current_state: str
    next_state: str
    approval_required: bool
    approval: dict[str, Any]
    plan: dict[str, Any]
    execution: dict[str, Any]
    final_response: dict[str, Any]
    evidence_events: list[dict[str, Any]]
