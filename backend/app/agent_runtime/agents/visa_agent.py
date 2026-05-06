from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.agents.rag_support import evidence_refs_for_query
from app.agent_runtime.schemas.agent_output import (
    AgentOutput,
    AgentRiskFlag,
    ApprovalRequiredAction,
)
from app.agent_runtime.tools.visa_risk_tool import calculate_visa_timeline


VISA_SOURCE_IDS = [
    "law_immigration_act_001",
    "law_foreign_worker_act_001",
    "gov24_stay_extension_001",
    "hikorea_stay_guide_001",
]


def assess_visa_status(request: Mapping[str, Any]) -> AgentOutput:
    input_state = request.get("input_state") if isinstance(request.get("input_state"), Mapping) else {}
    evidence_sources = evidence_refs_for_query(
        "E-9 체류기간 연장 체류만료 출입국관리법 외국인근로자법 HiKorea 정부24",
        expected_source_ids=VISA_SOURCE_IDS,
    )
    timeline = calculate_visa_timeline(input_state)
    risk_flags = [
        AgentRiskFlag(
            type=str(flag),
            level="high" if flag in {"visa_expired", "visa_expiry_urgent"} else "medium",
            reason=_risk_reason(str(flag)),
            source_agent="visa_document_agent",
            source_ids=[source.source_id for source in evidence_sources],
        )
        for flag in timeline.get("risk_flags", [])
    ]
    missing_inputs = ["visa_expires_at"] if timeline.get("status") == "needs_more_information" else []

    return AgentOutput(
        agent_id="visa_document_agent",
        status="draft",
        summary="체류만료일과 계약종료일을 계산했으며, 비자 가능 여부는 확정하지 않습니다.",
        checklist=[
            "체류만료일 기준 D-day 확인",
            "계약종료일과 체류만료일 충돌 여부 확인",
            "체류기간 연장 관련 공식 안내 근거 확인",
            "행정사 또는 담당자 검토 필요 여부 표시",
        ],
        missing_inputs=missing_inputs,
        risk_flags=risk_flags,
        evidence_sources=evidence_sources,
        approval_required_actions=[
            ApprovalRequiredAction(
                action_type="expert_review",
                label="행정사 검토 요청",
                reason="AI는 체류 연장 가능 여부를 확정하지 않으며 전문가 검토가 필요합니다.",
                source_agent="visa_document_agent",
            )
        ],
        next_actions=[
            "체류만료 D-day와 계약종료일 충돌 여부를 담당자가 검토해 주세요.",
            "필요 시 행정사에게 체류 관련 검토를 요청해 주세요.",
        ],
        raw={
            "visa_timeline": timeline,
            "eligibility_decision": None,
            "legal_advice_provided": False,
        },
    )


def _risk_reason(flag: str) -> str:
    reasons = {
        "missing_visa_expiry_date": "체류만료일이 없어 D-day 계산을 완료할 수 없습니다.",
        "visa_expired": "체류만료일이 이미 지났습니다.",
        "visa_expiry_urgent": "체류만료일이 14일 이내입니다.",
        "visa_expiry_near": "체류만료일이 60일 이내입니다.",
        "visa_expiry_watch": "체류만료일이 90일 이내입니다.",
        "contract_after_visa_expiry": "계약종료일이 체류만료일보다 늦습니다.",
    }
    return reasons.get(flag, "체류 관련 담당자 확인이 필요합니다.")
