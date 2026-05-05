from app.agent_runtime.graph.workflow import run_workflow


def test_run_workflow_routes_and_masks_input_and_appends_events() -> None:
    result = run_workflow(
        {
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
        }
    )

    assert result["case_type"] == "new_hiring"
    assert result["current_state"] == "site_check"
    assert result["next_state"] == "candidate_intake"
    assert result["detected_intents"] == ["HIRING", "VISA_CHECK"]
    assert "workforce_agent" in result["plan"]["required_agents"]
    assert "visa_document_agent" in result["plan"]["required_agents"]
    assert result["approval"]["required"] is True
    assert result["input_state"]["alien_number"] == "900101-▲▲▲▲▲▲▲"
    assert len(result["evidence_events"]) >= 5


def test_run_workflow_blocks_guardrail_violations() -> None:
    result = run_workflow(
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


def test_run_workflow_moves_to_handoff_when_human_approved() -> None:
    result = run_workflow(
        {
            "request_id": "req_003",
            "user_id": "user_003",
            "company_id": "company_003",
            "user_message": "신규 채용 초안 작성해줘.",
            "case_type": "new_hiring",
            "human_approved": True,
            "input_state": {"requested_headcount": 3},
        }
    )

    assert result["approval"]["status"] == "APPROVED"
    assert result["current_state"] == "handoff_package"
    assert result["next_state"] == "completed"
    assert result["status"] == "completed"
