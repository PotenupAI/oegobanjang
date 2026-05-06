from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.agents.rag_support import evidence_refs_for_query
from app.agent_runtime.schemas.agent_output import AgentOutput, ApprovalRequiredAction
from app.agent_runtime.tools.document_check_tool import calculate_missing_documents
from app.agent_runtime.tools.handoff_package_tool import build_handoff_package


def build_document_package(request: Mapping[str, Any]) -> AgentOutput:
    input_state = request.get("input_state") if isinstance(request.get("input_state"), Mapping) else {}
    case_type = str(request.get("case_type") or input_state.get("case_type") or "new_hiring")
    visa_type = str(input_state.get("visa_type") or "E-9")
    document_gap = calculate_missing_documents(
        {
            "case_type": case_type,
            "visa_type": visa_type,
            "held_documents": input_state.get("held_documents") or input_state.get("documents") or [],
            "db_document_state": input_state.get("db_document_state"),
            "document_state": input_state.get("document_state"),
        }
    )
    missing_documents = list(document_gap.get("output", {}).get("missing_documents", []))
    required_documents = list(document_gap.get("output", {}).get("required_documents", []))
    citation_ids = list(document_gap.get("citations", []))
    evidence_sources = evidence_refs_for_query(
        "E-9 서류 체크리스트 고용변동 신고서 체류기간 연장 제출 서류 고용허가 신청",
        expected_source_ids=_preferred_source_ids(case_type, citation_ids),
    )
    source_ids = [source.source_id for source in evidence_sources]
    package = build_handoff_package(
        {
            "case_type": case_type,
            "visa_type": visa_type,
            "worker_name": input_state.get("worker_name"),
            "missing_documents": missing_documents,
            "evidence_source_ids": source_ids,
        }
    )

    return AgentOutput(
        agent_id="document_package_agent",
        status="draft",
        summary="필수 서류와 누락 서류를 계산하고 행정사 전달 패키지 초안을 만들었습니다.",
        checklist=[
            "케이스별 필수 서류 확인",
            "보유 서류와 누락 서류 비교",
            "공식 근거 source_id 첨부",
            "외부 전달 전 담당자 승인 대기",
        ],
        required_documents=required_documents,
        missing_documents=missing_documents,
        evidence_sources=evidence_sources,
        approval_required_actions=[
            ApprovalRequiredAction(
                action_type="send_expert_package",
                label="행정사에게 패키지 전달",
                reason="행정사 전달은 외부 전달 작업이므로 담당자 승인이 필요합니다.",
                source_agent="document_package_agent",
            )
        ],
        next_actions=["담당자가 누락 서류와 evidence source_id를 검토한 뒤 전달 여부를 승인해 주세요."],
        raw={"document_gap": document_gap, "handoff_package": package},
    )


def _preferred_source_ids(case_type: str, citation_ids: list[str]) -> list[str]:
    preferred = {
        "new_hiring": ["eps_employer_process_001", "eps_application_guide_001"],
        "stay_extension": ["gov24_stay_extension_001", "hikorea_stay_guide_001"],
        "employment_change": ["law_form_employment_change_001", "gov24_workplace_change_001"],
    }.get(case_type, [])
    return list(dict.fromkeys([*citation_ids, *preferred]))
