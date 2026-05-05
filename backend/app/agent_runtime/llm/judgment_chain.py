from __future__ import annotations

from typing import Any

from app.agent_runtime.guardrails import check_output

from .client import JudgmentClient
from .parser import WorkBridgeJudgmentReport, parse_judgment_json
from .prompts import build_judgment_messages


def run_judgment_chain(
    *,
    user_message: str,
    detected_intents: list[str],
    evidence_package: dict[str, Any],
    client: JudgmentClient,
) -> WorkBridgeJudgmentReport:
    messages = build_judgment_messages(
        user_message=user_message,
        detected_intents=detected_intents,
        evidence_package=evidence_package,
    )
    judgment = parse_judgment_json(client.generate_json(messages))
    violations = check_output(judgment.model_dump(mode="json"))
    if not violations:
        return judgment

    return judgment.model_copy(
        update={
            "status": "blocked",
            "blocked": True,
            "approval_required": True,
            "guardrail_notes": sorted(set(judgment.guardrail_notes + violations)),
        }
    )
