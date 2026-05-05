from __future__ import annotations

from typing import Any

from app.agent_runtime.llm.parser import WorkBridgeJudgmentReport
from app.agent_runtime.middleware.pii_filter import mask_payload

from .risk import normalize_risk_flags


def build_basic_report(judgment: WorkBridgeJudgmentReport) -> dict[str, Any]:
    risk_flags = normalize_risk_flags(
        [risk_flag.model_dump(mode="json") for risk_flag in judgment.risk_flags]
    )
    evidence_source_ids = _evidence_source_ids(judgment, risk_flags)
    approval_status = "PENDING" if judgment.approval_required else "NOT_REQUIRED"

    report = {
        "request_id": judgment.request_id,
        "case_type": judgment.case_type,
        "approval_required": judgment.approval_required,
        "readiness_status": judgment.readiness_status,
        "risk_flags": risk_flags,
        "evidence_source_ids": evidence_source_ids,
        "sections": [
            {"title": "요청 요약", "body": judgment.summary},
            {"title": "감지된 업무 의도", "body": ", ".join(judgment.detected_intents)},
            {
                "title": "확인된 공식/템플릿 근거",
                "body": _format_evidence_summary(judgment),
            },
            {"title": "위험도 분류", "body": _format_risk_flags(risk_flags)},
            {
                "title": "승인 필요한 작업",
                "body": f"{approval_status}: approval_required={judgment.approval_required}",
            },
            {"title": "다음 조치", "body": "\n".join(judgment.next_actions)},
            {"title": "Evidence source_id 목록", "body": ", ".join(evidence_source_ids)},
        ],
    }
    return mask_payload(report)


def _evidence_source_ids(
    judgment: WorkBridgeJudgmentReport,
    risk_flags: list[dict[str, Any]],
) -> list[str]:
    source_ids: list[str] = []
    for evidence in judgment.evidence_summary:
        source_ids.append(evidence.source_id)
    for flag in risk_flags:
        source_ids.extend(flag["source_ids"])
    return sorted(set(source_ids))


def _format_evidence_summary(judgment: WorkBridgeJudgmentReport) -> str:
    return "\n".join(
        f"- {item.claim} (source_id={item.source_id}, grade={item.evidence_grade})"
        for item in judgment.evidence_summary
    )


def _format_risk_flags(risk_flags: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {flag['type']} [{flag['level']}]: {flag['reason']}"
        for flag in risk_flags
    )
