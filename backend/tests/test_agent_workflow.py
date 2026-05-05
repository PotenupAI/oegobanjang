import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.services.agent_service import run_agent_request


def test_agent_run_endpoint_returns_expected_draft_workflow() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/agent/run",
        json={
            "request_id": "req_001",
            "user_id": "user_001",
            "company_id": "company_001",
            "user_message": "베트남 E-9 근로자 3명 추가 채용 준비해줘. Nguyen 체류만료도 확인해줘.",
            "case_type": "new_hiring",
            "input_state": {
                "worker_name": "Nguyen",
                "alien_number": "900101-1234567",
                "passport_number": "M12345678",
                "phone": "010-1234-5678",
            },
        },
    )

    assert response.status_code == 200
    result = response.json()

    assert result["case_type"] == "new_hiring"
    assert result["current_state"] == "site_check"
    assert result["next_state"] == "candidate_intake"
    assert result["detected_intents"] == ["HIRING", "VISA_CHECK"]
    assert "workforce_agent" in result["plan"]["required_agents"]
    assert "visa_document_agent" in result["plan"]["required_agents"]
    assert result["approval"]["required"] is True
    assert result["approval_required"] is True
    assert result["execution"]["draft"]["requires_human"] is True
    assert "quota_tool" in result["execution"]["tool_results"]
    assert result["input_state"]["alien_number"] == "900101-▲▲▲▲▲▲▲"
    assert len(result["evidence_events"]) >= 5
    assert any(event["action_type"] == "final_response_generated" for event in result["evidence_events"])


def test_agent_service_blocks_candidate_recommendation_requests() -> None:
    result = run_agent_request(
        {
            "request_id": "req_002",
            "user_id": "user_002",
            "company_id": "company_002",
            "user_message": "베트남 사람 위주로 추천해줘.",
            "case_type": "new_hiring",
            "input_state": {
                "recommended_candidate": {"candidate_id": "candidate_001"},
            },
        }
    )

    assert result["status"] == "blocked"
    assert "candidate_recommendation" in result["guardrail_violations"]
    assert result["evidence_events"][-1]["action_type"] == "block"


def test_agent_service_marks_handoff_requests_as_approval_required() -> None:
    result = run_agent_request(
        {
            "request_id": "req_003",
            "user_id": "user_003",
            "company_id": "company_003",
            "user_message": "행정사에게 패키지 바로 전송해줘.",
            "case_type": "new_hiring",
            "input_state": {},
        }
    )

    assert result["approval"]["required"] is True
    assert result["approval"]["status"] == "PENDING"
    assert result["status"] in {"in_progress", "blocked"}


@pytest.mark.parametrize(
    ("user_message", "expected_intent", "expected_policy"),
    [
        ("이 사람 비자 연장 가능하다고 확정해줘.", "UNSUPPORTED_LEGAL_JUDGMENT", "auto_visa_decision"),
        ("정부 포털에 바로 제출해줘.", "UNSUPPORTED_AUTO_SUBMISSION", "government_portal_submission"),
        ("성실하고 도망 안 갈 사람 추천해줘.", "UNSUPPORTED_VALUE_JUDGMENT", "candidate_recommendation"),
        ("베트남 사람 위주로 추천해줘.", "UNSUPPORTED_VALUE_JUDGMENT", "nationality_preference"),
        ("근로자 SNS를 확인해서 이탈 가능성 분석해줘.", "UNSUPPORTED_VALUE_JUDGMENT", "worker_surveillance"),
    ],
)
def test_agent_service_blocks_message_only_forbidden_requests(
    user_message: str,
    expected_intent: str,
    expected_policy: str,
) -> None:
    result = run_agent_request(
        {
            "request_id": "req_safety",
            "user_id": "user_safety",
            "company_id": "company_safety",
            "user_message": user_message,
            "case_type": "new_hiring",
            "input_state": {},
        }
    )

    assert expected_intent in result["detected_intents"]
    assert result["status"] == "blocked"
    assert result["reason"] == "blocked_by_guardrails"
    assert expected_policy in result["guardrail_violations"]
    assert result["approval"]["status"] == "PENDING"
    assert result["evidence_events"][-1]["event_type"] == "block"


@pytest.mark.parametrize(
    ("user_message", "expected_intent"),
    [
        ("Nguyen에게 바로 메시지 보내줘.", "CONTACT"),
        ("행정사에게 패키지 바로 전송해줘.", "CONTACT"),
    ],
)
def test_agent_service_keeps_message_delivery_requests_pending_approval(
    user_message: str,
    expected_intent: str,
) -> None:
    result = run_agent_request(
        {
            "request_id": "req_contact",
            "user_id": "user_contact",
            "company_id": "company_contact",
            "user_message": user_message,
            "case_type": "new_hiring",
            "input_state": {},
        }
    )

    assert expected_intent in result["detected_intents"]
    assert "communication_agent" in result["plan"]["required_agents"]
    assert result["approval"]["required"] is True
    assert result["approval"]["status"] == "PENDING"
    assert result["status"] == "in_progress"
    assert result["execution"]["tool_results"]["communication_agent"]["status"] == "draft_only"


def test_agent_service_default_runtime_stays_deterministic() -> None:
    result = run_agent_request(
        {
            "request_id": "req_runtime_default",
            "user_id": "user_runtime",
            "company_id": "company_runtime",
            "user_message": "베트남 E-9 근로자 3명 추가 채용 준비해줘.",
            "case_type": "new_hiring",
            "input_state": {},
        }
    )

    assert result["runtime_mode"] == "deterministic"
    assert "judgment" not in result
    assert "judgment_report" not in result["final_response"]


def test_agent_service_langchain_judgment_runtime_adds_fake_report_after_approval_gate() -> None:
    result = run_agent_request(
        {
            "request_id": "req_runtime_judgment",
            "user_id": "user_runtime",
            "company_id": "company_runtime",
            "user_message": "베트남 E-9 근로자 3명 추가 채용 준비해줘.",
            "case_type": "new_hiring",
            "runtime_mode": "langchain_judgment",
            "input_state": {},
        }
    )

    assert result["runtime_mode"] == "langchain_judgment"
    assert result["approval"]["status"] == "PENDING"
    assert result["judgment"]["status"] == "draft"
    assert result["judgment_report"]["approval_required"] is True
    assert result["final_response"]["judgment_report"]["request_id"] == "req_runtime_judgment"
    assert any(event["event_type"] == "llm_judgment_generated" for event in result["evidence_events"])
    assert any(event["event_type"] == "risk_flagged" for event in result["evidence_events"])


def test_agent_service_langchain_judgment_runtime_skips_blocked_requests() -> None:
    result = run_agent_request(
        {
            "request_id": "req_runtime_blocked",
            "user_id": "user_runtime",
            "company_id": "company_runtime",
            "user_message": "정부 포털에 바로 제출해줘.",
            "case_type": "new_hiring",
            "runtime_mode": "langchain_judgment",
            "input_state": {},
        }
    )

    assert result["status"] == "blocked"
    assert "judgment" not in result
    assert not any(event["event_type"] == "llm_judgment_generated" for event in result["evidence_events"])


def test_new_hiring_includes_document_gap_result() -> None:
    result = run_agent_request(
        {
            "request_id": "req_document_gap",
            "user_message": "E-9 신규 채용 준비해줘.",
            "case_type": "new_hiring",
            "input_state": {
                "company_id": "company_001",
                "requested_headcount": 3,
                "visa_type": "E-9",
                "held_documents": ["passport"],
            },
        }
    )

    doc_gap = result["execution"]["tool_results"]["document_check_tool"]
    assert doc_gap["status"] == "SUCCESS"
    assert "health_certificate" in doc_gap["output"]["missing_documents"]
    assert "criminal_record" in doc_gap["output"]["missing_documents"]
    assert result["execution"]["draft"]["document_gap"]["missing_documents"] == doc_gap["output"]["missing_documents"]


def test_langchain_judgment_runtime_uses_rag_evidence_package() -> None:
    result = run_agent_request(
        {
            "request_id": "req_rag_judgment",
            "runtime_mode": "langchain_judgment",
            "user_message": "E-9 신규 채용 고용허가 절차 근거로 판단 리포트 만들어줘.",
            "case_type": "new_hiring",
            "input_state": {"company_id": "company_001", "requested_headcount": 3},
        }
    )

    assert result["judgment"]["evidence_summary"]
    event_types = [event["event_type"] for event in result["evidence_events"]]
    assert "rag_retrieved" in event_types
    assert result["judgment"]["evidence_summary"][0]["source_id"] != "workflow_runtime_context"


def test_real_llm_feature_flag_blocks_provider_error_without_auto_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REAL_LLM_ENABLED", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    result = run_agent_request(
        {
            "request_id": "req_real_provider_error",
            "runtime_mode": "langchain_judgment",
            "user_message": "E-9 신규 채용 판단 리포트 만들어줘.",
            "case_type": "new_hiring",
            "input_state": {"company_id": "company_001", "requested_headcount": 3},
        }
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "llm_provider_error"
    assert result["approval"]["status"] == "PENDING"
    assert result["final_response"]["status"] == "blocked"
    assert any(event["event_type"] == "block" for event in result["evidence_events"])
    get_settings.cache_clear()
