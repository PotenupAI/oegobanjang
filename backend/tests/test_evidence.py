import json

from fastapi.testclient import TestClient

from app.agent_runtime.graph.workflow import run_workflow
from app.main import create_app
from app.schemas.evidence import EvidenceCreate
from app.services.evidence_service import (
    append_evidence,
    contains_raw_pii,
    list_evidence,
    reset_evidence_store,
    validate_required_order,
)


def test_workflow_emits_required_evidence_events_without_raw_pii() -> None:
    result = run_workflow(
        {
            "request_id": "req_ev_001",
            "user_id": "user_ev_001",
            "company_id": "company_ev_001",
            "user_message": "베트남 E-9 근로자 3명 추가 채용 준비해줘.",
            "case_type": "new_hiring",
            "input_state": {
                "worker_name": "Nguyen",
                "alien_number": "900101-1234567",
                "passport_number": "M12345678",
                "phone": "010-1234-5678",
            },
        }
    )

    action_types = [event["action_type"] for event in result["evidence_events"]]
    event_types = [event["event_type"] for event in result["evidence_events"]]

    assert "route" in action_types
    assert "plan" in action_types
    assert "execute_tool" in action_types
    assert "approve" in action_types
    assert "intent_classified" in event_types
    assert "plan_created" in event_types
    assert "tool_executed" in event_types
    assert "approval_requested" in event_types
    assert "approval_completed" in event_types
    assert "final_response_generated" in event_types
    assert "final_response_generated" in action_types
    assert "900101-1234567" not in json.dumps(result, ensure_ascii=False)
    assert validate_required_order(result["evidence_events"]) is True
    assert contains_raw_pii(result) is False


def test_workflow_handoff_event_keeps_approval_required_true() -> None:
    result = run_workflow(
        {
            "request_id": "req_ev_002",
            "user_id": "user_ev_002",
            "company_id": "company_ev_002",
            "user_message": "행정사에게 패키지 바로 전송해줘.",
            "case_type": "new_hiring",
            "input_state": {},
        }
    )

    assert result["approval_required"] is True
    assert result["final_response"]["approval_required"] is True


def test_evidence_service_is_idempotent_and_masks_payload() -> None:
    reset_evidence_store()
    payload = EvidenceCreate(
        request_id="req_ev_store_001",
        event_type="approval_requested",
        agent_id="approval_gate",
        action_type="approve",
        payload={"alien_number": "900101-1234567", "phone": "010-1234-5678"},
    )

    first = append_evidence(payload)
    second = append_evidence(payload)
    events = list_evidence("req_ev_store_001")

    assert first.event_id == second.event_id
    assert len(events) == 1
    assert "900101-1234567" not in json.dumps(events[0].payload, ensure_ascii=False)
    assert "010-1234-5678" not in json.dumps(events[0].payload, ensure_ascii=False)


def test_evidence_api_appends_and_reads_request_events_without_raw_pii() -> None:
    reset_evidence_store()
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/evidence",
        json={
            "request_id": "req_api_evidence",
            "event_type": "final_response_generated",
            "agent_id": "final_response",
            "action_type": "final_response_generated",
            "payload": {"passport_number": "M12345678"},
        },
    )
    assert created.status_code == 200

    listed = client.get("/api/v1/evidence/req_api_evidence")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body["events"]) == 1
    assert "M12345678" not in json.dumps(body, ensure_ascii=False)
