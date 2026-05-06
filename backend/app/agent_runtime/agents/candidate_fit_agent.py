from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.agents.rag_support import evidence_refs_for_query
from app.agent_runtime.schemas.agent_output import AgentOutput, AgentRiskFlag


REQUIRED_CANDIDATE_FIELDS = ("passport", "visa_type", "photo", "available_start_date")


def evaluate_candidate_fit(request: Mapping[str, Any]) -> AgentOutput:
    input_state = request.get("input_state") if isinstance(request.get("input_state"), Mapping) else {}
    candidates = input_state.get("candidates") if isinstance(input_state.get("candidates"), list) else []
    evidence_sources = evidence_refs_for_query(
        "E-9 후보자 서류 준비 항목 고용허가 절차 후보 확인 항목",
        expected_source_ids=["eps_employer_process_001", "eps_application_guide_001"],
    )

    reviewed: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_map = candidate if isinstance(candidate, Mapping) else {}
        missing_fields = [
            field
            for field in REQUIRED_CANDIDATE_FIELDS
            if not _field_present(candidate_map.get(field))
        ]
        reviewed.append(
            {
                "candidate_id": str(candidate_map.get("candidate_id") or f"candidate_{index:03d}"),
                "name": str(candidate_map.get("name") or ""),
                "status": "needs_information" if missing_fields else "ready_for_review",
                "verified_fields": [
                    field
                    for field in REQUIRED_CANDIDATE_FIELDS
                    if _field_present(candidate_map.get(field))
                ],
                "missing_fields": missing_fields,
                "manager_review_required": True,
            }
        )
        missing_inputs.extend([f"candidate.{field}" for field in missing_fields])

    if not candidates:
        missing_inputs.append("candidates")

    risk_flags = []
    if missing_inputs:
        risk_flags.append(
            AgentRiskFlag(
                type="candidate_information_incomplete",
                level="medium",
                reason="후보자를 점수화하지 않고 서류와 입력 누락만 확인했습니다.",
                source_agent="candidate_fit_agent",
                source_ids=[source.source_id for source in evidence_sources],
            )
        )

    return AgentOutput(
        agent_id="candidate_fit_agent",
        status="draft",
        summary="후보 적합성은 점수화하지 않고 필수 확인 항목의 누락 여부만 정리했습니다.",
        checklist=[
            "후보자 여권 보유 여부 확인",
            "체류자격 또는 고용허가 절차상 확인 항목 입력",
            "사진 및 근무 가능일 확인",
            "담당자 검토 전 후보 추천 또는 순위화 금지",
        ],
        missing_inputs=sorted(set(missing_inputs)),
        risk_flags=risk_flags,
        evidence_sources=evidence_sources,
        next_actions=["누락된 후보 서류와 근무 가능일을 담당자가 확인해 주세요."],
        raw={"candidates": reviewed, "ranking_performed": False, "recommendation_performed": False},
    )


def _field_present(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return value not in (None, "", [], {})
