from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.agents.rag_support import evidence_refs_for_query
from app.agent_runtime.schemas.agent_output import AgentOutput, ApprovalRequiredAction, EvidenceSourceRef


def build_case_briefing(request: Mapping[str, Any]) -> AgentOutput:
    case_type = str(request.get("case_type") or "new_hiring")
    input_state = request.get("input_state") if isinstance(request.get("input_state"), Mapping) else {}
    raw_agent_outputs = request.get("agent_outputs") if isinstance(request.get("agent_outputs"), Mapping) else {}
    agent_summaries = _agent_summaries(raw_agent_outputs)
    missing_inputs = _dedupe(
        item
        for output in raw_agent_outputs.values()
        if isinstance(output, Mapping)
        for item in output.get("missing_inputs", [])
    )
    next_actions = _dedupe(
        item
        for output in raw_agent_outputs.values()
        if isinstance(output, Mapping)
        for item in output.get("next_actions", [])
    )
    evidence_sources = _dedupe_evidence_sources(
        [
            *_evidence_from_agent_outputs(raw_agent_outputs),
            *evidence_refs_for_query(
                _briefing_query(case_type),
                expected_source_ids=_preferred_source_ids(case_type),
            ),
        ]
    )

    summary = _summary(case_type, input_state, agent_summaries)
    return AgentOutput(
        agent_id="briefing_agent",
        status="draft",
        summary=summary,
        checklist=[
            "케이스 목적과 현재 입력 상태 요약",
            "하위 agent 결과의 누락 입력과 다음 조치 통합",
            "공식 근거 source_id 첨부",
            "내부 공유 전 담당자 승인 대기",
        ],
        missing_inputs=missing_inputs,
        evidence_sources=evidence_sources,
        approval_required_actions=[
            ApprovalRequiredAction(
                action_type="share_internal_briefing",
                label="내부 브리핑 공유",
                reason="보고 또는 공유용 브리핑은 담당자 검토 후 공유되어야 합니다.",
                source_agent="briefing_agent",
            )
        ],
        next_actions=next_actions or ["담당자가 브리핑 초안의 누락 입력과 근거 source_id를 검토해 주세요."],
        raw={
            "briefing_type": "internal_case_briefing",
            "case_type": case_type,
            "agent_summaries": agent_summaries,
            "input_snapshot": {
                "company_id": input_state.get("company_id"),
                "worker_name": input_state.get("worker_name"),
                "requested_headcount": input_state.get("requested_headcount"),
                "industry": input_state.get("industry"),
                "visa_type": input_state.get("visa_type"),
            },
            "sent": False,
            "shared": False,
            "exported": False,
        },
    )


def _summary(case_type: str, input_state: Mapping[str, Any], agent_summaries: list[str]) -> str:
    case_label = {
        "new_hiring": "신규 채용",
        "stay_extension": "체류기간 연장",
        "employment_change": "고용변동",
        "workplace_change_intake": "사업장 변경",
    }.get(case_type, case_type)
    headcount = input_state.get("requested_headcount")
    prefix = f"{case_label} 케이스"
    if headcount:
        prefix = f"{prefix} {headcount}명"
    if agent_summaries:
        return f"{prefix}의 현재 준비 상태를 브리핑 초안으로 정리했습니다."
    return f"{prefix}의 입력 상태를 기준으로 브리핑 초안을 만들었습니다."


def _agent_summaries(raw_agent_outputs: Mapping[str, Any]) -> list[str]:
    summaries: list[str] = []
    for agent_id, output in raw_agent_outputs.items():
        if not isinstance(output, Mapping):
            continue
        summary = str(output.get("summary") or "").strip()
        if summary:
            summaries.append(f"{agent_id}: {summary}")
    return summaries


def _evidence_from_agent_outputs(raw_agent_outputs: Mapping[str, Any]) -> list[EvidenceSourceRef]:
    refs: list[EvidenceSourceRef] = []
    for output in raw_agent_outputs.values():
        if not isinstance(output, Mapping):
            continue
        for source in output.get("evidence_sources", []):
            if isinstance(source, EvidenceSourceRef):
                refs.append(source)
            elif isinstance(source, Mapping) and source.get("source_id"):
                refs.append(EvidenceSourceRef.model_validate(source))
    return refs


def _briefing_query(case_type: str) -> str:
    if case_type == "stay_extension":
        return "E-9 체류기간 연장 절차 서류 기한 담당자 검토"
    if case_type in {"employment_change", "workplace_change_intake"}:
        return "고용변동 신고서 사업장 변경 외국인근로자 신고 절차"
    return "E-9 신규 채용 고용허가 사업주 절차 허용업종 서류"


def _preferred_source_ids(case_type: str) -> list[str]:
    if case_type == "stay_extension":
        return ["gov24_stay_extension_001", "hikorea_stay_guide_001"]
    if case_type in {"employment_change", "workplace_change_intake"}:
        return ["law_form_employment_change_001", "gov24_workplace_change_001"]
    return ["eps_employer_process_001", "eps_application_guide_001", "eps_allowed_industries_001"]


def _dedupe(values: Any) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _dedupe_evidence_sources(values: list[EvidenceSourceRef]) -> list[EvidenceSourceRef]:
    deduped: list[EvidenceSourceRef] = []
    seen: set[str] = set()
    for value in values:
        source_id = value.source_id
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        deduped.append(value)
    return deduped
