from app.agent_runtime.graph.nodes.approval_gate import evaluate_approval
from app.main import create_app
from app.schemas.approval import ApprovalCreate, ApprovalDecision
from app.services.approval_service import (
    create_approval,
    decide_approval,
    list_approvals,
    reset_approval_store,
)
from fastapi.testclient import TestClient


def test_approval_gate_requires_human_approval_for_handoff_requests() -> None:
    approval = evaluate_approval({"approval_required": True, "human_approved": False})

    assert approval["required"] is True
    assert approval["status"] == "PENDING"


def test_approval_gate_marks_approved_when_human_flag_present() -> None:
    approval = evaluate_approval({"approval_required": True, "human_approved": True})

    assert approval["required"] is True
    assert approval["status"] == "APPROVED"


def test_approval_service_is_idempotent_by_request_and_action() -> None:
    reset_approval_store()
    payload = ApprovalCreate(
        request_id="req_approval_001",
        action_type="send_expert_package",
        reason="handoff requires manager approval",
    )

    first = create_approval(payload)
    second = create_approval(payload)

    assert first.approval_id == second.approval_id
    assert len(list_approvals("req_approval_001")) == 1
    assert second.status == "PENDING"


def test_approval_service_tracks_approval_decision() -> None:
    reset_approval_store()
    record = create_approval(
        ApprovalCreate(request_id="req_approval_002", action_type="send_worker_message")
    )

    decided = decide_approval(record.approval_id, ApprovalDecision(status="REJECTED"))

    assert decided is not None
    assert decided.status == "REJECTED"
    assert decided.decided_at is not None


def test_approval_api_creates_lists_and_decides_requests() -> None:
    reset_approval_store()
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/approvals",
        json={"request_id": "req_api_approval", "action_type": "export_handoff_package"},
    )
    assert created.status_code == 200
    approval_id = created.json()["approval_id"]

    listed = client.get("/api/v1/approvals", params={"request_id": "req_api_approval"})
    assert listed.status_code == 200
    assert len(listed.json()["approvals"]) == 1

    decided = client.post(f"/api/v1/approvals/{approval_id}/decision", json={"status": "APPROVED"})
    assert decided.status_code == 200
    assert decided.json()["status"] == "APPROVED"
