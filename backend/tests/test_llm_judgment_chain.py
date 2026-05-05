from __future__ import annotations

import pytest

from app.agent_runtime.llm.client import FakeJudgmentClient
from app.agent_runtime.llm.judgment_chain import run_judgment_chain
from app.agent_runtime.llm.parser import parse_judgment_json
from app.agent_runtime.llm.prompts import build_judgment_messages


def _evidence_package() -> dict[str, object]:
    return {
        "status": "ready",
        "request_id": "req_001",
        "query": "베트남 E-9 근로자 3명 추가 채용 준비해줘.",
        "case_type": "new_hiring",
        "retrieved_chunks": [
            {
                "chunk_id": "seed_eps_procedure_demo_001__0001",
                "source_id": "seed_eps_procedure_demo_001",
                "title": "E-9 고용허가 절차",
                "text": "내국인 구인노력 후 고용허가 신청을 준비한다.",
                "evidence_grade": "B",
                "doc_type": "procedure",
                "citation": {
                    "source_id": "seed_eps_procedure_demo_001",
                    "chunk_id": "seed_eps_procedure_demo_001__0001",
                    "title": "E-9 고용허가 절차",
                    "publisher": "MVP seed placeholder",
                    "url": "",
                    "evidence_grade": "B",
                },
            }
        ],
        "citations": [],
        "missing_evidence": [],
        "evidence_policy": {
            "answer_evidence_grades": ["A", "B", "E"],
            "excluded_grades": ["C", "D", "F"],
            "synthetic_official_claims_allowed": False,
        },
    }


def _valid_judgment_json() -> str:
    return """
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


def test_build_judgment_messages_separates_system_user_and_evidence() -> None:
    messages = build_judgment_messages(
        user_message="E-9 신규 채용 준비해줘.",
        detected_intents=["HIRING"],
        evidence_package=_evidence_package(),
    )

    assert [message["role"] for message in messages] == ["system", "developer", "user", "evidence"]
    assert "법률" in messages[0]["content"]
    assert "JSON" in messages[1]["content"]
    assert "E-9 신규 채용 준비해줘." in messages[2]["content"]
    assert "seed_eps_procedure_demo_001" in messages[3]["content"]


def test_parse_judgment_json_accepts_valid_contract() -> None:
    judgment = parse_judgment_json(_valid_judgment_json())

    assert judgment.status == "draft"
    assert judgment.request_id == "req_001"
    assert judgment.risk_flags[0].type == "missing_documents"
    assert judgment.approval_required is True


@pytest.mark.parametrize(
    "raw",
    [
        'Here is the JSON: {"status": "draft"}',
        '{"status": "draft"} trailing text',
    ],
)
def test_parse_judgment_json_rejects_non_json_only_output(raw: str) -> None:
    with pytest.raises(ValueError, match="JSON-only"):
        parse_judgment_json(raw)


def test_parse_judgment_json_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="Invalid judgment JSON"):
        parse_judgment_json('{"status":"draft","request_id":"req_001"}')


def test_parse_judgment_json_rejects_invalid_enum() -> None:
    raw = _valid_judgment_json().replace('"missing_documents"', '"new_unapproved_risk"')

    with pytest.raises(ValueError, match="Invalid judgment JSON"):
        parse_judgment_json(raw)


def test_run_judgment_chain_uses_fake_client_without_network() -> None:
    client = FakeJudgmentClient(response_text=_valid_judgment_json())

    judgment = run_judgment_chain(
        user_message="E-9 신규 채용 준비해줘.",
        detected_intents=["HIRING", "VISA_CHECK"],
        evidence_package=_evidence_package(),
        client=client,
    )

    assert client.calls == 1
    assert judgment.status == "draft"
    assert judgment.evidence_summary[0].source_id == "seed_eps_procedure_demo_001"


def test_run_judgment_chain_blocks_guardrail_violating_llm_output() -> None:
    raw = _valid_judgment_json().replace(
        '"prohibited_actions": []',
        '"prohibited_actions": [{"government_portal_submission": {"submitted": true}}]',
    )
    client = FakeJudgmentClient(response_text=raw)

    judgment = run_judgment_chain(
        user_message="정부 포털에 제출해줘.",
        detected_intents=["UNSUPPORTED_AUTO_SUBMISSION"],
        evidence_package=_evidence_package(),
        client=client,
    )

    assert judgment.status == "blocked"
    assert judgment.blocked is True
    assert "government_portal_submission" in judgment.guardrail_notes
