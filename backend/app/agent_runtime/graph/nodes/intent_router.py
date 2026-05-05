from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.guardrails import check_text_policy_violations
from app.agent_runtime.graph.state import CASE_STATE_TRANSITIONS, CaseType


def route_intent(payload: Mapping[str, Any]) -> dict[str, Any]:
    case_type = _normalize_case_type(payload.get("case_type"))
    current_state, next_state = CASE_STATE_TRANSITIONS.get(case_type, ("blocked", "blocked"))
    detected_intents = _detect_intents(payload)

    return {
        "case_type": case_type,
        "current_state": current_state,
        "next_state": next_state,
        "detected_intents": detected_intents,
        "guardrail_violations": check_text_policy_violations(str(payload.get("user_message", ""))),
    }


def _normalize_case_type(raw_case_type: Any) -> CaseType | str:
    if raw_case_type in CASE_STATE_TRANSITIONS:
        return raw_case_type
    return str(raw_case_type or "unknown")


def _detect_intents(payload: Mapping[str, Any]) -> list[str]:
    user_message = str(payload.get("user_message", "")).lower()
    case_type = payload.get("case_type")
    policy_violations = check_text_policy_violations(user_message)

    intents: list[str] = []
    if "government_portal_submission" in policy_violations:
        intents.append("UNSUPPORTED_AUTO_SUBMISSION")
    if "auto_visa_decision" in policy_violations or "legal_advice" in policy_violations:
        intents.append("UNSUPPORTED_LEGAL_JUDGMENT")
    if any(
        violation in policy_violations
        for violation in (
            "candidate_recommendation",
            "nationality_preference",
            "worker_surveillance",
            "absconding_prediction",
            "worker_reliability_scoring",
        )
    ):
        intents.append("UNSUPPORTED_VALUE_JUDGMENT")

    if any(intent.startswith("UNSUPPORTED_") for intent in intents):
        return _dedupe(intents)

    if case_type == "workplace_change_intake":
        intents.append("WORKPLACE_CHANGE")
    if _contains_any(user_message, ("채용", "hiring", "hire", "추가 채용", "신규채용")):
        intents.append("HIRING")
    if _contains_any(user_message, ("비자", "visa", "체류", "만료", "passport", "e-9", "e9", "출입국")):
        intents.append("VISA_CHECK")
    if _contains_any(user_message, ("서류 누락", "누락 여부", "문서 확인", "document check", "서류 확인")):
        intents.append("DOCUMENT_CHECK")
    if _contains_any(user_message, ("메시지", "문자", "카톡", "발송", "전송", "보내줘", "보내")):
        intents.append("CONTACT")
    if _contains_any(user_message, ("브리핑", "요약", "보고", "briefing", "brief")):
        intents.append("BRIEFING")

    return _dedupe(intents)


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
