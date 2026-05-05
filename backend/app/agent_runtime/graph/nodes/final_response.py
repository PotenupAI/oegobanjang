from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_final_response(context: Mapping[str, Any]) -> dict[str, Any]:
    response = {
        "summary": "workflow completed",
        "case_type": context.get("case_type"),
        "current_state": context.get("current_state"),
        "next_state": context.get("next_state"),
        "approval_status": context.get("approval", {}).get("status"),
        "approval_required": context.get("approval", {}).get("required", True),
        "draft": context.get("execution", {}).get("draft"),
        "tool_results": context.get("execution", {}).get("tool_results", {}),
    }
    if context.get("judgment_report"):
        response["judgment_report"] = context["judgment_report"]
    return response
