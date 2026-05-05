from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def evaluate_approval(context: Mapping[str, Any]) -> dict[str, Any]:
    required = bool(context.get("approval_required", True))
    approved = bool(context.get("human_approved"))
    if context.get("execution", {}).get("blocked_reason"):
        return {
            "required": required,
            "status": "PENDING",
            "reason": context["execution"]["blocked_reason"],
        }

    return {
        "required": required,
        "status": "APPROVED" if approved else "PENDING",
        "reason": "human approval required before handoff" if required else "no approval needed",
    }
