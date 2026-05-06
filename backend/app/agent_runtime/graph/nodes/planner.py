from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def create_plan(context: Mapping[str, Any]) -> dict[str, Any]:
    case_type = context.get("case_type")
    detected_intents = list(context.get("detected_intents", []))
    guardrail_violations = list(context.get("guardrail_violations", []))

    if any(intent.startswith("UNSUPPORTED_") for intent in detected_intents):
        return {
            "case_type": case_type,
            "required_agents": [],
            "steps": ["route_request", "block_for_safety", "prepare_safe_response"],
            "blocked_reason": "blocked_by_guardrails",
            "guardrail_violations": guardrail_violations,
        }

    required_agents: list[str] = []
    if "HIRING" in detected_intents or case_type in {"new_hiring", "workplace_change_intake"}:
        required_agents.append("workforce_agent")
    if "CANDIDATE_REVIEW" in detected_intents:
        required_agents.append("candidate_fit_agent")
    if "VISA_CHECK" in detected_intents:
        required_agents.append("visa_document_agent")
    if "DOCUMENT_CHECK" in detected_intents and "visa_document_agent" not in required_agents:
        required_agents.append("visa_document_agent")
    if "DOCUMENT_CHECK" in detected_intents:
        required_agents.append("document_package_agent")
    if "HANDOFF" in detected_intents:
        required_agents.append("document_package_agent")
        required_agents.append("approval_handoff_agent")
    if "CONTACT" in detected_intents:
        required_agents.append("communication_agent")
        required_agents.append("approval_handoff_agent")
    if "BRIEFING" in detected_intents:
        required_agents.append("briefing_agent")
    if case_type == "workplace_change_intake":
        required_agents.append("handoff_package_agent")

    return {
        "case_type": case_type,
        "required_agents": _dedupe(required_agents),
        "steps": _build_steps(case_type, detected_intents),
    }


def _build_steps(case_type: Any, detected_intents: list[str]) -> list[str]:
    steps = ["route_request", "build_plan", "execute_workflow", "request_approval", "prepare_handoff"]
    if case_type == "workplace_change_intake" and "VISA_CHECK" not in detected_intents:
        steps.insert(2, "collect_workplace_details")
    return steps


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
