from app.agent_runtime.guardrails import (
    FORBIDDEN_BEHAVIORS,
    check_output,
    check_text_policy_violations,
    enforce_guardrails,
)


def test_check_output_blocks_candidate_recommendation_and_nationality_preference() -> None:
    output = {
        "recommended_candidate": {"candidate_id": "candidate_001"},
        "nationality_preference": "베트남 사람 위주로 추천",
    }

    violations = check_output(output)

    assert "candidate_recommendation" in violations
    assert "nationality_preference" in violations


def test_check_output_blocks_legal_decision_and_external_submission() -> None:
    output = {
        "visa_decision": "approved",
        "legal_advice": "비자 연장이 가능합니다.",
        "external_submission": {"target": "government_portal", "submitted": True},
    }

    violations = check_output(output)

    assert "auto_visa_decision" in violations
    assert "legal_advice" in violations
    assert "external_submission_without_approval" in violations


def test_check_output_allows_approval_required_draft() -> None:
    output = {
        "draft_message": "여권 사본 제출 요청 메시지 초안",
        "approval_required": True,
        "external_submission": {"target": "expert_handoff", "submitted": False},
    }

    assert check_output(output) == []


def test_enforce_guardrails_returns_blocked_result_with_reason() -> None:
    output = {
        "status": "ready",
        "candidate_score": {"candidate_id": "candidate_001", "reliability": 0.91},
    }

    guarded = enforce_guardrails(output)

    assert guarded["status"] == "blocked"
    assert guarded["violations"] == ["worker_reliability_scoring"]
    assert "blocked_by_guardrails" in guarded["reason"]


def test_forbidden_behaviors_are_stable_policy_ids() -> None:
    assert "candidate_recommendation" in FORBIDDEN_BEHAVIORS
    assert "nationality_preference" in FORBIDDEN_BEHAVIORS
    assert "auto_visa_decision" in FORBIDDEN_BEHAVIORS
    assert "external_submission_without_approval" in FORBIDDEN_BEHAVIORS


def test_check_text_policy_violations_detects_message_only_forbidden_requests() -> None:
    assert check_text_policy_violations("이 사람 비자 연장 가능하다고 확정해줘.") == [
        "auto_visa_decision"
    ]
    assert check_text_policy_violations("정부 포털에 바로 제출해줘.") == [
        "government_portal_submission"
    ]
    assert check_text_policy_violations("성실하고 도망 안 갈 사람 추천해줘.") == [
        "candidate_recommendation",
        "absconding_prediction",
        "worker_reliability_scoring",
    ]
    assert check_text_policy_violations("베트남 사람 위주로 추천해줘.") == [
        "nationality_preference"
    ]
    assert check_text_policy_violations("근로자 SNS를 확인해서 이탈 가능성 분석해줘.") == [
        "worker_surveillance",
        "absconding_prediction",
    ]
