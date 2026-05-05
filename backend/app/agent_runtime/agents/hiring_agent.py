from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_hiring_draft(request: Mapping[str, Any]) -> dict[str, Any]:
    case_type = str(request.get("case_type") or "")
    input_state = request.get("input_state") if isinstance(request.get("input_state"), Mapping) else {}
    retrieved_evidence = request.get("retrieved_evidence") if isinstance(request.get("retrieved_evidence"), Mapping) else {}

    if case_type == "new_hiring":
        draft = {
            "site_checklist": _build_site_checklist(input_state, retrieved_evidence),
            "required_documents": _required_documents_for_new_hiring(),
            "questions_for_employer_or_partner": _questions_for_new_hiring(input_state),
            "risk_flags": _risk_flags_for_new_hiring(input_state, retrieved_evidence),
            "requires_human": True,
        }
        return draft

    if case_type == "workplace_change_intake":
        return {
            "status": "blocked",
            "reason": "workplace_change_intake_minimally_supported",
            "site_checklist": [],
            "required_documents": [],
            "questions_for_employer_or_partner": [
                "사업장 변경 사유와 현재 상태를 확인해 주세요.",
            ],
            "risk_flags": ["workplace_change_history_unverified"],
            "requires_human": True,
        }

    return {
        "status": "blocked",
        "reason": "unsupported_case_type",
        "site_checklist": [],
        "required_documents": [],
        "questions_for_employer_or_partner": [],
        "risk_flags": ["unsupported_case_type"],
        "requires_human": True,
    }


def _build_site_checklist(input_state: Mapping[str, Any], retrieved_evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    checklist: list[dict[str, Any]] = [
        {"item": "사업장 정보 확인", "status": "pending"},
        {"item": "채용 인원 확인", "status": "pending"},
        {"item": "체류만료일 확인", "status": "pending"},
    ]

    if input_state.get("worker_name"):
        checklist.append({"item": "근로자 기본정보 확인", "status": "pending", "worker_name": input_state["worker_name"]})
    if retrieved_evidence.get("source_id"):
        checklist.append({"item": "공식 근거 확인", "status": "pending", "source_id": retrieved_evidence["source_id"]})

    return checklist


def _required_documents_for_new_hiring() -> list[str]:
    return [
        "사업장 기본정보",
        "근로자 여권 사본",
        "근로자 체류정보",
        "고용 예정 인원",
    ]


def _questions_for_new_hiring(input_state: Mapping[str, Any]) -> list[str]:
    questions = [
        "현재 채용하려는 인원과 직무를 입력해 주세요.",
        "사업장 내 배치 예정 장소를 알려 주세요.",
    ]
    if not input_state.get("company_id"):
        questions.append("사업장 식별 정보가 비어 있습니다. company_id를 확인해 주세요.")
    return questions


def _risk_flags_for_new_hiring(
    input_state: Mapping[str, Any],
    retrieved_evidence: Mapping[str, Any],
) -> list[str]:
    risk_flags: list[str] = []
    if not input_state.get("company_id"):
        risk_flags.append("missing_company_id")
    if not input_state.get("requested_headcount") and not input_state.get("headcount"):
        risk_flags.append("missing_headcount")
    if retrieved_evidence and not retrieved_evidence.get("source_id"):
        risk_flags.append("missing_evidence_source")
    return risk_flags
