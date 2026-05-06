# Mission 015: Workforce Subagents

## Goal

인력 확보 Agent(`workforce_agent`) 아래에서 필요한 5개 업무 agent를 실제 코드로 구현하고, 이미 수집된 RAG 근거를 사용해 채용 준비, 후보 확인, 체류 리스크, 서류 패키징, 사람 승인 대기 출력을 생성한다.

이 mission은 후보 추천기나 자동 제출 시스템을 만드는 작업이 아니다. 각 agent는 공식 근거와 현재 입력 상태를 정리하고, 외부 발송·전달·완료 처리는 항상 승인 대기 상태로 남긴다.

## Required Reading

```txt
AGENTS.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/AI_OS_DESIGN.md
docs/RAG_STRATEGY.md
docs/TOOL_CONTRACT.md
docs/SECURITY_GUARDRAILS.md
docs/EVIDENCE_LOG_SCHEMA.md
missions/active/014-agent-output-aggregation.md
missions/completed/002-rag-indexing.md
missions/completed/008-rag-evidence-package.md
```

## Target Files

```txt
backend/app/agent_runtime/agents/hiring_agent.py
backend/app/agent_runtime/agents/candidate_fit_agent.py
backend/app/agent_runtime/agents/visa_agent.py
backend/app/agent_runtime/agents/document_package_agent.py
backend/app/agent_runtime/agents/approval_handoff_agent.py
backend/app/agent_runtime/agents/rag_support.py
backend/app/agent_runtime/tools/visa_risk_tool.py
backend/app/agent_runtime/tools/handoff_package_tool.py
backend/app/agent_runtime/graph/nodes/intent_router.py
backend/app/agent_runtime/graph/nodes/planner.py
backend/app/agent_runtime/graph/nodes/executor.py
backend/app/agent_runtime/graph/nodes/approval_gate.py
backend/app/agent_runtime/graph/nodes/aggregator.py
backend/app/agent_runtime/graph/nodes/final_response.py
backend/app/agent_runtime/graph/workflow.py
backend/app/agent_runtime/schemas/agent_output.py
backend/tests/test_workforce_agents.py
backend/tests/test_agent_aggregation.py
backend/tests/test_agent_workflow.py
backend/tests/test_document_check_tool.py
data-pipeline/seed/document_requirements.csv
```

## Scope

- Implement workforce requirement/matching output without candidate recommendation.
- Implement candidate fit review as missing-field/status review only.
- Implement visa/stay timeline risk calculation without legal eligibility decisions.
- Implement document checklist and handoff package draft output.
- Implement human approval/expert handoff output as approval-required only.
- Align `document_requirements.csv` source IDs with real RAG manifest source IDs.
- Return standard `AgentOutput` records through `execution.agent_outputs`.
- Merge agent outputs into `aggregated_output` for approval and final response.

## Out of Scope

- Real DB persistence for worker/candidate/document state.
- Real external message sending.
- Government portal submission.
- Legal, visa, or labor eligibility final decisions.
- Candidate ranking, scoring, nationality preference, reliability scoring, or absconding prediction.
- Production LLM provider calls.
- Frontend UI changes.

## Acceptance Criteria

- `workforce_agent`, `candidate_fit_agent`, `visa_document_agent`, `document_package_agent`, and `approval_handoff_agent` can all return standard `AgentOutput`.
- RAG source references include real manifest IDs such as `eps_employer_process_001`, `eps_allowed_industries_001`, `eps_application_guide_001`, `gov24_stay_extension_001`, `law_foreign_worker_act_001`, and `law_form_employment_change_001`.
- Candidate review does not include score, rank, recommendation, nationality preference, or reliability judgment.
- Visa/stay output includes D-day and risk flags but no eligibility decision.
- Document package output is draft-only and includes `sent=false`, `exported=false`, and approval-required actions.
- Workflow output includes top-level `aggregated_output`.
- Approval gate reads `aggregated_output.approval_required_actions`.
- Existing safety guardrails remain enforced.

## Verification Commands

```bash
uv run pytest backend/tests/test_workforce_agents.py
uv run pytest backend/tests/test_agent_aggregation.py
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_workflow_state.py backend/tests/test_approvals.py
uv run pytest backend/tests/test_document_check_tool.py backend/tests/test_rag_source_manifest.py backend/tests/test_rag_eval_dataset.py backend/tests/test_evidence_package.py
uv run pytest backend/tests
uv run python scripts/run_evals.py --dataset workflow_e2e_cases --strict
uv run python scripts/run_evals.py --dataset rag_retrieval_cases --strict
uv run python scripts/run_evals.py --dataset safety_guardrail_cases --strict
```

## Human Review Checklist

- [ ] Agent들이 하나의 거대 agent로 합쳐지지 않았는가?
- [ ] 후보 추천·점수화·국적 선호·성실도 판단을 하지 않는가?
- [ ] 비자 가능 여부나 법률 판단을 확정하지 않는가?
- [ ] 외부 발송/전달/제출/완료 처리가 자동 실행되지 않는가?
- [ ] RAG source_id가 실제 manifest source_id와 맞는가?
- [ ] Evidence Log와 final response에 raw PII가 새로 유입되지 않는가?
