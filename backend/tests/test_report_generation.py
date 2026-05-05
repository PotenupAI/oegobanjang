from __future__ import annotations

import pytest

from app.agent_runtime.llm.parser import parse_judgment_json
from app.agent_runtime.reporting.report import build_basic_report
from app.agent_runtime.reporting.risk import normalize_risk_flags


def _judgment():
    return parse_judgment_json(
        """
{
  "status": "draft",
  "request_id": "req_001",
  "case_type": "new_hiring",
  "detected_intents": ["HIRING", "VISA_CHECK"],
  "summary": "E-9 신규 채용과 체류만료 확인 요청입니다.",
  "evidence_summary": [
    {
      "claim": "고용허가 신청 전 절차 확인이 필요합니다.",
      "source_id": "seed_eps_procedure_demo_001",
      "evidence_grade": "B"
    }
  ],
  "risk_flags": [
    {
      "type": "missing_documents",
      "level": "medium",
      "reason": "여권 사본 제출 여부가 확인되지 않았습니다.",
      "source_ids": ["seed_eps_procedure_demo_001"]
    }
  ],
  "readiness_status": "needs_review",
  "missing_inputs": ["여권 사본 제출 여부"],
  "follow_up_questions": ["여권 사본을 제출했나요?"],
  "approval_required": true,
  "blocked": false,
  "guardrail_notes": [],
  "prohibited_actions": [],
  "next_actions": ["담당자가 누락 서류를 확인합니다."]
}
""".strip()
    )


def test_normalize_risk_flags_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="Unsupported risk flag type"):
        normalize_risk_flags(
            [
                {
                    "type": "invented_risk",
                    "level": "medium",
                    "reason": "bad",
                    "source_ids": [],
                }
            ]
        )


def test_build_basic_report_contains_required_sections_and_evidence_ids() -> None:
    report = build_basic_report(_judgment())

    assert report["request_id"] == "req_001"
    assert report["approval_required"] is True
    assert [section["title"] for section in report["sections"]] == [
        "요청 요약",
        "감지된 업무 의도",
        "확인된 공식/템플릿 근거",
        "위험도 분류",
        "승인 필요한 작업",
        "다음 조치",
        "Evidence source_id 목록",
    ]
    assert report["evidence_source_ids"] == ["seed_eps_procedure_demo_001"]
    assert report["risk_flags"][0]["type"] == "missing_documents"
    assert "PENDING" in report["sections"][4]["body"]


def test_build_basic_report_masks_sensitive_text() -> None:
    judgment = _judgment().model_copy(
        update={
            "summary": "Nguyen 900101-1234567 M12345678 010-1234-5678 확인",
            "missing_inputs": ["900101-1234567"],
        }
    )

    report = build_basic_report(judgment)
    rendered = str(report)

    assert "900101-1234567" not in rendered
    assert "M12345678" not in rendered
    assert "010-1234-5678" not in rendered
    assert "▲" in rendered
