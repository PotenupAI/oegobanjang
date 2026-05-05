from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


FORBIDDEN_BEHAVIORS = [
    "candidate_recommendation",
    "nationality_preference",
    "auto_visa_decision",
    "legal_advice",
    "labor_advice",
    "government_portal_submission",
    "external_submission_without_approval",
    "worker_surveillance",
    "absconding_prediction",
    "worker_reliability_scoring",
    "public_workplace_reputation_scoring",
    "broker_detection",
]


def check_output(case_output: dict[str, Any]) -> list[str]:
    """Return guardrail policy IDs violated by an agent output."""
    violations: list[str] = []
    _scan_for_violations(case_output, violations)
    return _dedupe(violations)


def check_text_policy_violations(text: str) -> list[str]:
    normalized = text.lower()
    violations: list[str] = []

    if _contains_any(normalized, ("정부 포털", "정부포털", "portal")) and _contains_any(
        normalized,
        ("제출", "submit"),
    ):
        violations.append("government_portal_submission")

    if _contains_any(normalized, ("확정", "가능하다고", "가능 여부")) and _contains_any(
        normalized,
        ("비자", "연장", "체류"),
    ):
        violations.append("auto_visa_decision")

    if _contains_any(normalized, ("법률 자문", "법적 자문", "노무 자문")):
        violations.append("legal_advice")

    if _contains_any(normalized, ("베트남 사람 위주", "국적별", "국적 위주", "국적 선호")):
        violations.append("nationality_preference")

    if "nationality_preference" not in violations and _contains_any(normalized, ("성실", "추천")) and _contains_any(
        normalized,
        ("사람", "후보", "근로자"),
    ):
        violations.append("candidate_recommendation")

    if _contains_any(normalized, ("sns", "단톡", "커뮤니티 감시", "국적 커뮤니티")):
        violations.append("worker_surveillance")

    if _contains_any(normalized, ("도망", "이탈 가능성", "이탈 위험")):
        violations.append("absconding_prediction")

    if _contains_any(normalized, ("성실", "신뢰도", "평가 점수")):
        violations.append("worker_reliability_scoring")

    return _dedupe(violations)


def enforce_guardrails(case_output: dict[str, Any]) -> dict[str, Any]:
    violations = check_output(case_output)
    if not violations:
        return case_output

    return {
        **case_output,
        "status": "blocked",
        "reason": "blocked_by_guardrails",
        "violations": violations,
    }


def _append_if_present(
    violations: list[str],
    output: Mapping[str, Any],
    field: str,
    policy_id: str,
) -> None:
    if output.get(field) not in (None, False, "", [], {}):
        violations.append(policy_id)


def _scan_for_violations(value: Any, violations: list[str]) -> None:
    if isinstance(value, Mapping):
        _append_if_present(violations, value, "recommended_candidate", "candidate_recommendation")
        _append_if_present(violations, value, "ranked_candidates", "candidate_recommendation")
        _append_if_present(violations, value, "nationality_preference", "nationality_preference")
        _append_if_present(violations, value, "preferred_nationality", "nationality_preference")
        _append_if_present(violations, value, "legal_advice", "legal_advice")
        _append_if_present(violations, value, "labor_advice", "labor_advice")
        _append_if_present(violations, value, "sns_monitoring", "worker_surveillance")
        _append_if_present(violations, value, "community_monitoring", "worker_surveillance")
        _append_if_present(violations, value, "absconding_prediction", "absconding_prediction")
        _append_if_present(violations, value, "escape_risk_score", "absconding_prediction")
        _append_if_present(violations, value, "candidate_score", "worker_reliability_scoring")
        _append_if_present(violations, value, "reliability_score", "worker_reliability_scoring")
        _append_if_present(
            violations,
            value,
            "public_workplace_reputation_score",
            "public_workplace_reputation_scoring",
        )
        _append_if_present(violations, value, "broker_detection", "broker_detection")

        if _has_auto_visa_decision(value):
            violations.append("auto_visa_decision")

        if _has_government_portal_submission(value):
            violations.append("government_portal_submission")

        if _has_external_submission_without_approval(value):
            violations.append("external_submission_without_approval")

        for nested in value.values():
            _scan_for_violations(nested, violations)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _scan_for_violations(nested, violations)


def _has_auto_visa_decision(output: Mapping[str, Any]) -> bool:
    decision = str(output.get("visa_decision", "")).lower()
    eligibility = str(output.get("visa_eligibility", "")).lower()
    final_judgment = output.get("final_legal_judgment")
    return decision in {"approved", "denied", "eligible", "ineligible"} or eligibility in {
        "eligible",
        "ineligible",
        "approved",
        "denied",
    } or final_judgment not in (None, False, "", [], {})


def _has_government_portal_submission(output: Mapping[str, Any]) -> bool:
    submission = output.get("government_portal_submission")
    if isinstance(submission, Mapping):
        return bool(submission.get("submitted"))
    return submission not in (None, False, "", [], {})


def _has_external_submission_without_approval(output: Mapping[str, Any]) -> bool:
    submission = output.get("external_submission")
    if not isinstance(submission, Mapping):
        return submission not in (None, False, "", [], {}) and not bool(output.get("approval_required"))

    submitted = bool(submission.get("submitted"))
    approval_required = bool(output.get("approval_required"))
    approved = bool(output.get("human_approved") or submission.get("human_approved"))
    return submitted and (not approval_required or not approved)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)
