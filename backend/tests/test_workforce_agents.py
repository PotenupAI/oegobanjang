from __future__ import annotations

from app.agent_runtime.agents.approval_handoff_agent import prepare_approval_handoff
from app.agent_runtime.agents.candidate_fit_agent import evaluate_candidate_fit
from app.agent_runtime.agents.document_package_agent import build_document_package
from app.agent_runtime.agents.hiring_agent import build_workforce_requirements
from app.agent_runtime.agents.visa_agent import assess_visa_status
from app.agent_runtime.tools.handoff_package_tool import build_handoff_package
from app.agent_runtime.tools.visa_risk_tool import calculate_visa_timeline


def test_workforce_requirements_uses_official_rag_sources_without_recommending_candidates() -> None:
    output = build_workforce_requirements(
        {
            "case_type": "new_hiring",
            "input_state": {
                "company_id": "company_001",
                "requested_headcount": 3,
                "industry": "manufacturing",
                "job_role": "용접",
                "housing_available": True,
            },
        }
    )

    assert output.agent_id == "workforce_agent"
    assert output.status == "draft"
    assert "candidate_recommendation" not in output.raw
    source_ids = {source.source_id for source in output.evidence_sources}
    assert {
        "eps_employer_process_001",
        "eps_allowed_industries_001",
        "eps_application_guide_001",
    } <= source_ids
    assert "requested_headcount" not in output.missing_inputs
    assert any("송출회사" in action or "행정사" in action for action in output.next_actions)


def test_candidate_fit_agent_checks_missing_fields_without_scoring_or_ranking() -> None:
    output = evaluate_candidate_fit(
        {
            "input_state": {
                "candidates": [
                    {
                        "candidate_id": "cand_001",
                        "name": "Nguyen",
                        "passport": True,
                        "photo": False,
                        "available_start_date": "2026-06-01",
                    }
                ]
            }
        }
    )

    assert output.agent_id == "candidate_fit_agent"
    assert output.status == "draft"
    assert output.raw["candidates"][0]["candidate_id"] == "cand_001"
    assert output.raw["candidates"][0]["missing_fields"] == ["visa_type", "photo"]
    assert "score" not in output.raw["candidates"][0]
    assert "rank" not in output.raw["candidates"][0]
    assert any(flag.type == "candidate_information_incomplete" for flag in output.risk_flags)


def test_visa_agent_calculates_d_day_but_does_not_decide_eligibility() -> None:
    timeline = calculate_visa_timeline(
        {
            "visa_expires_at": "2026-07-15",
            "contract_ends_at": "2026-07-31",
            "today": "2026-05-06",
        }
    )
    output = assess_visa_status(
        {
            "case_type": "new_hiring",
            "input_state": {
                "worker_name": "Nguyen",
                "visa_type": "E-9",
                "visa_expires_at": "2026-07-15",
                "contract_ends_at": "2026-07-31",
                "today": "2026-05-06",
            },
        }
    )

    assert timeline["d_day"] == 70
    assert output.agent_id == "visa_document_agent"
    assert output.raw["visa_timeline"]["d_day"] == 70
    assert output.raw["eligibility_decision"] is None
    assert any(flag.type == "contract_after_visa_expiry" for flag in output.risk_flags)
    assert any(action.action_type == "expert_review" for action in output.approval_required_actions)


def test_document_package_agent_creates_draft_only_handoff_package() -> None:
    package = build_handoff_package(
        {
            "case_type": "new_hiring",
            "visa_type": "E-9",
            "worker_name": "Nguyen",
            "missing_documents": ["criminal_record"],
            "evidence_source_ids": ["eps_employer_process_001"],
        }
    )
    output = build_document_package(
        {
            "case_type": "new_hiring",
            "input_state": {
                "visa_type": "E-9",
                "worker_name": "Nguyen",
                "held_documents": ["passport"],
            },
        }
    )

    assert package["status"] == "draft"
    assert package["sent"] is False
    assert package["exported"] is False
    assert "eps_employer_process_001" in package["evidence_source_ids"]
    assert output.agent_id == "document_package_agent"
    assert output.missing_documents
    assert any(action.action_type == "send_expert_package" for action in output.approval_required_actions)


def test_approval_handoff_agent_keeps_external_actions_pending() -> None:
    output = prepare_approval_handoff(
        {
            "input_state": {"worker_name": "Nguyen"},
            "requested_actions": ["send_worker_message", "send_expert_package", "complete_case"],
        }
    )

    assert output.agent_id == "approval_handoff_agent"
    assert output.status == "draft"
    assert output.raw["sent"] is False
    assert output.raw["case_completed"] is False
    assert {action.action_type for action in output.approval_required_actions} == {
        "send_worker_message",
        "send_expert_package",
        "complete_case",
    }
