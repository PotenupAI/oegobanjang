from __future__ import annotations

from typing import Any, TypedDict


class WorkflowEvidenceEvent(TypedDict, total=False):
    timestamp: str
    work_item_id: str
    agent_id: str
    action_type: str
    input: dict[str, Any]
    output: dict[str, Any]
    confidence: float
    human_override: bool
    evidence_chunk_ids: list[str]


class WorkflowExecutionState(TypedDict, total=False):
    request_id: str
    user_id: str
    company_id: str
    user_message: str
    case_type: str
    current_state: str
    next_state: str
    detected_intents: list[str]
    input_state: dict[str, Any]
    plan: dict[str, Any]
    execution: dict[str, Any]
    approval: dict[str, Any]
    approval_required: bool
    evidence_events: list[WorkflowEvidenceEvent]
    final_response: dict[str, Any]
    status: str
    guardrail_violations: list[str]
    reason: str
    draft: dict[str, Any]
