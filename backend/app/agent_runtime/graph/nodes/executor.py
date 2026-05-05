from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.agents.hiring_agent import build_hiring_draft
from app.agent_runtime.tools.document_check_tool import calculate_missing_documents
from app.agent_runtime.tools.quota_tool import assess_readiness


def execute_plan(context: Mapping[str, Any]) -> dict[str, Any]:
    plan = context.get("plan") if isinstance(context.get("plan"), Mapping) else {}
    input_state = context.get("input_state") if isinstance(context.get("input_state"), Mapping) else {}
    case_type = context.get("case_type")
    required_agents = list(plan.get("required_agents", []))

    tool_results: dict[str, Any] = {}
    drafts: dict[str, Any] = {}
    blocked_reason: str | None = str(plan.get("blocked_reason") or "") or None
    guardrail_violations = list(plan.get("guardrail_violations", []))

    if blocked_reason:
        return {
            "status": "blocked",
            "executed_agents": [],
            "tool_results": {},
            "drafts": {},
            "draft": None,
            "blocked_reason": blocked_reason,
            "guardrail_violations": guardrail_violations,
        }

    if "workforce_agent" in required_agents:
        hiring_payload = {
            "case_type": case_type,
            "current_state": context.get("current_state"),
            "input_state": input_state,
            "retrieved_evidence": context.get("retrieved_evidence", {}),
        }
        draft = build_hiring_draft(hiring_payload)
        drafts["workforce_agent"] = draft
        tool_results["quota_tool"] = assess_readiness(hiring_payload)
        document_gap = calculate_missing_documents(
            {
                "case_type": case_type,
                "visa_type": input_state.get("visa_type") or "E-9",
                "held_documents": input_state.get("held_documents") or input_state.get("documents") or [],
            }
        )
        tool_results["document_check_tool"] = document_gap
        if isinstance(draft, dict):
            draft["document_gap"] = {
                "required_documents": document_gap.get("output", {}).get("required_documents", []),
                "missing_documents": document_gap.get("output", {}).get("missing_documents", []),
                "citations": document_gap.get("citations", []),
            }
        if draft.get("status") == "blocked":
            blocked_reason = str(draft.get("reason") or "hiring_agent_blocked")

    if "visa_document_agent" in required_agents:
        tool_results["visa_document_agent"] = {
            "status": "mocked",
            "reason": "visa_document_agent placeholder",
        }
    if "communication_agent" in required_agents:
        tool_results["communication_agent"] = {
            "status": "draft_only",
            "approval_required": True,
            "sent": False,
            "reason": "external messages require human approval before delivery",
        }
    if "briefing_agent" in required_agents:
        tool_results["briefing_agent"] = {
            "status": "mocked",
            "reason": "briefing_agent placeholder",
        }

    output: dict[str, Any] = {
        "status": "blocked" if blocked_reason else "executed",
        "executed_agents": required_agents,
        "tool_results": tool_results,
        "drafts": drafts,
        "draft": drafts.get("workforce_agent"),
        "blocked_reason": blocked_reason,
        "guardrail_violations": guardrail_violations,
    }
    if input_state:
        output["input_echo"] = dict(input_state)
    return output
