from __future__ import annotations

from app.agent_runtime.graph.nodes.aggregator import aggregate_agent_outputs
from app.agent_runtime.graph.workflow import run_workflow
from app.agent_runtime.schemas.agent_output import AgentOutput, AggregatedCaseOutput


def test_agent_output_schema_defaults_are_safe() -> None:
    output = AgentOutput(agent_id="workforce_agent", summary="초안 생성")

    assert output.status == "draft"
    assert output.checklist == []
    assert output.approval_required_actions == []
    assert output.raw == {}


def test_aggregated_case_output_sets_approval_from_actions() -> None:
    aggregated = AggregatedCaseOutput(
        case_summary="검토 필요",
        approval_required_actions=[
            {
                "action_type": "send_expert_package",
                "label": "행정사에게 패키지 전달",
                "reason": "외부 전달은 담당자 승인이 필요합니다.",
                "source_agent": "approval_handoff_agent",
            }
        ],
    )

    assert aggregated.approval_required is True


def test_aggregator_merges_agent_outputs_without_creating_new_judgment() -> None:
    aggregated = aggregate_agent_outputs(
        {
            "execution": {
                "agent_outputs": {
                    "workforce_agent": AgentOutput(
                        agent_id="workforce_agent",
                        summary="채용 준비 초안",
                        checklist=["사업장 정보 확인"],
                        evidence_sources=[{"source_id": "eps_employer_process_001"}],
                    ).model_dump(mode="json"),
                    "approval_handoff_agent": AgentOutput(
                        agent_id="approval_handoff_agent",
                        summary="승인 대기",
                        approval_required_actions=[
                            {
                                "action_type": "send_expert_package",
                                "label": "행정사에게 패키지 전달",
                                "reason": "외부 전달은 담당자 승인이 필요합니다.",
                                "source_agent": "approval_handoff_agent",
                            }
                        ],
                    ).model_dump(mode="json"),
                }
            }
        }
    )

    assert aggregated["approval_required"] is True
    assert aggregated["combined_checklist"] == ["사업장 정보 확인"]
    assert aggregated["evidence_sources"][0]["source_id"] == "eps_employer_process_001"
    assert aggregated["agent_outputs"]["workforce_agent"]["summary"] == "채용 준비 초안"


def test_workflow_returns_workforce_subagent_outputs_and_aggregated_output() -> None:
    result = run_workflow(
        {
            "request_id": "req_workforce_subagents",
            "user_id": "user_001",
            "company_id": "company_001",
            "user_message": "E-9 신규 채용 후보 서류와 체류만료 확인하고 행정사 패키지 준비해줘.",
            "case_type": "new_hiring",
            "input_state": {
                "company_id": "company_001",
                "requested_headcount": 2,
                "industry": "manufacturing",
                "visa_type": "E-9",
                "visa_expires_at": "2026-07-15",
                "contract_ends_at": "2026-07-31",
                "today": "2026-05-06",
                "held_documents": ["passport"],
                "candidates": [
                    {
                        "candidate_id": "cand_001",
                        "name": "Nguyen",
                        "passport": True,
                        "photo": False,
                        "available_start_date": "2026-06-01",
                    }
                ],
            },
        }
    )

    assert result["status"] == "in_progress"
    assert set(result["execution"]["agent_outputs"]) >= {
        "workforce_agent",
        "candidate_fit_agent",
        "visa_document_agent",
        "document_package_agent",
        "approval_handoff_agent",
    }
    assert result["aggregated_output"]["approval_required"] is True
    assert result["aggregated_output"]["missing_documents"]
    assert result["final_response"]["aggregated_output"]["approval_required"] is True
    assert any(event["event_type"] == "agent_outputs_aggregated" for event in result["evidence_events"])
