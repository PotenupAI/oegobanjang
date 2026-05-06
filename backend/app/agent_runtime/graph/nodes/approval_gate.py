from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def evaluate_approval(context: Mapping[str, Any]) -> dict[str, Any]:
    aggregated = context.get("aggregated_output") if isinstance(context.get("aggregated_output"), Mapping) else {}
    required_actions = list(aggregated.get("approval_required_actions", []))
    required = bool(context.get("approval_required", True) or required_actions)
    approved = bool(context.get("human_approved"))
    if context.get("execution", {}).get("blocked_reason"):
        return {
            "required": required,
            "status": "PENDING",
            "reason": context["execution"]["blocked_reason"],
            "approval_required_actions": required_actions,
        }

    return {
        "required": required,
        "status": "APPROVED" if approved else "PENDING",
        "reason": "human approval required before handoff" if required else "no approval needed",
        "approval_required_actions": required_actions,
    }
