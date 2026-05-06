from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.agents.rag_support import evidence_refs_for_query
from app.agent_runtime.schemas.agent_output import AgentOutput, AgentRiskFlag


WORKFORCE_REQUIREMENT_SOURCE_IDS = [
    "eps_employer_process_001",
    "eps_allowed_industries_001",
    "eps_application_guide_001",
]


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


def build_workforce_requirements(request: Mapping[str, Any]) -> AgentOutput:
    input_state = request.get("input_state") if isinstance(request.get("input_state"), Mapping) else {}
    evidence_sources = evidence_refs_for_query(
        "E-9 신규 채용 고용허가 사업주 고용절차 허용업종 고용허가 신청 안내",
        expected_source_ids=WORKFORCE_REQUIREMENT_SOURCE_IDS,
    )
    missing_inputs = [
        field
        for field in ("company_id", "requested_headcount", "industry")
        if not input_state.get(field) and not request.get(field)
    ]
    requested_headcount = input_state.get("requested_headcount") or input_state.get("headcount")
    checklist = [
        "사업장 업종과 E-9 허용업종 해당 여부 확인",
        "내국인 구인노력 및 고용허가 신청 흐름 확인",
        "채용 인원, 직무, 배치 장소 입력 확인",
        "숙소, 안전교육, 근무조건 안내 준비",
    ]
    if requested_headcount:
        checklist.append(f"요청 인원 {requested_headcount}명 기준 준비 상태 확인")

    risk_flags = [
        AgentRiskFlag(
            type="missing_workforce_inputs",
            level="medium",
            reason="사업장, 인원, 업종 정보가 모두 있어야 신규 고용 준비 초안을 확정할 수 있습니다.",
            source_agent="workforce_agent",
            source_ids=[source.source_id for source in evidence_sources],
        )
    ] if missing_inputs else []

    return AgentOutput(
        agent_id="workforce_agent",
        status="draft",
        summary="E-9 신규 고용 준비 요건을 공식 절차 근거 기준으로 정리했습니다.",
        checklist=checklist,
        required_documents=_required_documents_for_new_hiring(),
        missing_inputs=missing_inputs,
        risk_flags=risk_flags,
        evidence_sources=evidence_sources,
        next_actions=[
            "송출회사 또는 행정사에게 후보군 확인 요청서에 들어갈 항목을 검토해 주세요.",
            "담당자가 사업장 조건과 채용 인원을 확인한 뒤 다음 단계로 넘겨 주세요.",
        ],
        raw={
            "case_type": request.get("case_type"),
            "industry": input_state.get("industry"),
            "job_role": input_state.get("job_role"),
            "housing_available": input_state.get("housing_available"),
            "allowed_source_ids": WORKFORCE_REQUIREMENT_SOURCE_IDS,
        },
    )


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
