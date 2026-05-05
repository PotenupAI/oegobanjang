from __future__ import annotations

from typing import Any, Literal, TypedDict


CaseType = Literal["new_hiring", "workplace_change_intake"]
ActionType = Literal[
    "route",
    "plan",
    "execute_tool",
    "approve",
    "final_response_generated",
    "block",
]


class EvidenceEvent(TypedDict, total=False):
    timestamp: str
    work_item_id: str
    agent_id: str
    event_type: str
    action_type: ActionType
    input: dict[str, Any]
    output: dict[str, Any]
    confidence: float
    human_override: bool
    evidence_chunk_ids: list[str]


class WorkflowState(TypedDict, total=False):
    request_id: str
    user_id: str
    company_id: str
    user_message: str
    case_type: CaseType
    current_state: str
    next_state: str
    detected_intents: list[str]
    input_state: dict[str, Any]
    plan: dict[str, Any]
    execution: dict[str, Any]
    approval: dict[str, Any]
    approval_required: bool
    evidence_events: list[EvidenceEvent]
    final_response: dict[str, Any]
    status: str
    guardrail_violations: list[str]
    reason: str
    draft: dict[str, Any]


CASE_STATE_TRANSITIONS: dict[CaseType, tuple[str, str]] = {
    "new_hiring": ("site_check", "candidate_intake"),
    "workplace_change_intake": ("site_check_and_intake", "contract_prep"),
}
