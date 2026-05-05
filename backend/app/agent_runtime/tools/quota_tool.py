from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def assess_readiness(payload: Mapping[str, Any]) -> dict[str, Any]:
    company_id = payload.get("company_id")
    current_state = payload.get("current_state")
    input_state = payload.get("input_state") if isinstance(payload.get("input_state"), Mapping) else {}

    missing_inputs: list[str] = []
    if not company_id:
        missing_inputs.append("company_id")
    if not current_state:
        missing_inputs.append("current_state")
    if not input_state.get("requested_headcount") and not input_state.get("headcount"):
        missing_inputs.append("requested_headcount")

    follow_up_questions: list[str] = []
    risk_flags: list[str] = []

    if missing_inputs:
        follow_up_questions.append("사업장, 상태, 인원 정보를 먼저 채워 주세요.")
        return {
            "readiness_status": "needs_more_information",
            "missing_inputs": missing_inputs,
            "follow_up_questions": follow_up_questions,
            "risk_flags": risk_flags,
            "requires_human": True,
        }

    available_quota = _read_int(input_state.get("available_quota"))
    requested_headcount = _read_int(input_state.get("requested_headcount") or input_state.get("headcount"))

    if requested_headcount is None:
        risk_flags.append("headcount_not_numeric")
        follow_up_questions.append("채용 인원을 숫자로 입력해 주세요.")
        return {
            "readiness_status": "needs_more_information",
            "missing_inputs": ["requested_headcount"],
            "follow_up_questions": follow_up_questions,
            "risk_flags": risk_flags,
            "requires_human": True,
        }

    if available_quota is not None and requested_headcount > available_quota:
        risk_flags.append("quota_insufficient")
        follow_up_questions.append("요청 인원이 현재 준비 가능 인원보다 많습니다.")
        return {
            "readiness_status": "needs_human_review",
            "missing_inputs": [],
            "follow_up_questions": follow_up_questions,
            "risk_flags": risk_flags,
            "requires_human": True,
        }

    return {
        "readiness_status": "ready_for_review",
        "missing_inputs": [],
        "follow_up_questions": follow_up_questions,
        "risk_flags": risk_flags,
        "requires_human": True,
    }


def _read_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
