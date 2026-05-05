from app.agent_runtime.langchain_runtime.judgment_agent import run_fake_langchain_judgment
from app.agent_runtime.langchain_runtime.tools import FORBIDDEN_TOOL_NAMES, SAFE_TOOL_NAMES, get_safe_tools


def test_langchain_adapter_registers_only_safe_tools() -> None:
    tools = get_safe_tools()

    assert set(tools) == SAFE_TOOL_NAMES
    assert set(tools).isdisjoint(FORBIDDEN_TOOL_NAMES)


def test_fake_langchain_judgment_uses_safe_tools_and_returns_structured_report() -> None:
    result = run_fake_langchain_judgment(
        request_id="req_langchain_001",
        user_message="E-9 신규 채용 고용허가 절차 근거로 판단 리포트 만들어줘.",
        case_type="new_hiring",
        detected_intents=["HIRING", "VISA_CHECK"],
        input_state={"company_id": "company_001", "requested_headcount": 3},
    )

    assert result.used_tools == ["retrieve_policy_context", "assess_readiness"]
    assert result.report.request_id == "req_langchain_001"
    assert result.report.approval_required is True
    assert result.report.evidence_summary
    assert result.retrieved_context
    assert all(item.evidence_grade in {"A", "B", "E"} for item in result.retrieved_context)


def test_fake_langchain_judgment_does_not_complete_missing_input_cases() -> None:
    result = run_fake_langchain_judgment(
        request_id="req_langchain_002",
        user_message="E-9 신규 채용 준비 상태를 확인해줘.",
        case_type="new_hiring",
        detected_intents=["HIRING"],
        input_state={},
    )

    assert result.report.approval_required is True
    assert result.report.readiness_status == "needs_review"
    assert "company_id" in result.report.missing_inputs
