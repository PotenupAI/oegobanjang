# Mission 014: Agent Output Aggregation

## Goal

인력 확보, 비자/서류, 다국어/소통 agent의 독립 실행 결과를 표준 schema로 맞추고, Aggregator node에서 하나의 WorkBridge case output으로 병합한다.

이 mission은 agent를 하나의 거대 agent로 합치는 작업이 아니다. 각 agent의 책임은 분리하고, 결과만 `aggregated_output`으로 수렴시키는 작업이다.

## Required Reading

```txt
AGENTS.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/AI_OS_DESIGN.md
docs/GRAPH_STATE.md
docs/TOOL_CONTRACT.md
docs/SECURITY_GUARDRAILS.md
docs/EVIDENCE_LOG_SCHEMA.md
docs/journal/journal.tn/progressive/history.md
docs/journal/journal.tn/progressive/진행상황.md
docs/superpowers/plans/2026-05-06-agent-output-aggregation.md
missions/completed/001-agent-runtime-skeleton.md
missions/completed/003-approval-evidence-log.md
missions/completed/011-judgment-runtime-mode.md
```

## Target Files

```txt
backend/app/agent_runtime/schemas/agent_output.py
backend/app/agent_runtime/graph/nodes/aggregator.py
backend/app/agent_runtime/graph/nodes/executor.py
backend/app/agent_runtime/graph/nodes/approval_gate.py
backend/app/agent_runtime/graph/nodes/final_response.py
backend/app/agent_runtime/graph/workflow.py
backend/tests/test_agent_aggregation.py
backend/tests/test_agent_workflow.py
backend/tests/test_eval_runner.py
scripts/run_evals.py
evals/datasets/workflow_e2e_cases.jsonl
```

## Scope

- Add standard `AgentOutput` schema.
- Add standard `AggregatedCaseOutput` schema.
- Add `aggregator.py` graph node.
- Make `executor.py` return `agent_outputs`.
- Preserve existing `draft`, `drafts`, `tool_results` compatibility fields.
- Make workflow call aggregator after executor.
- Make approval gate read `aggregated_output.approval_required_actions`.
- Make final response include `aggregated_output`.
- Add tests and eval checks for aggregated output.

## Out of Scope

- Real DB persistence for shared state.
- Real OpenAI/LangChain production provider call.
- Actual external message sending.
- Government portal submission.
- Legal/visa eligibility decision.
- Candidate recommendation or nationality preference.
- Full implementation of empty `visa_agent.py` or `contact_agent.py`.
- Frontend UI redesign.

## Acceptance Criteria

- `/api/v1/agent/run` response includes top-level `aggregated_output`.
- `execution.agent_outputs` includes agent-keyed standard outputs.
- `aggregated_output.agent_outputs.workforce_agent` exists for hiring requests.
- Communication/handoff requests add `approval_required_actions`.
- Approval gate returns `required=true` and `status=PENDING` for aggregated external actions.
- Final response includes `aggregated_output`.
- Existing workflow tests still pass.
- Evidence events include an aggregator event.
- Blocked requests remain blocked and do not bypass guardrails.
- No raw PII is introduced into aggregated output or evidence events.

## Verification Commands

```bash
uv run pytest backend/tests/test_agent_aggregation.py
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_approvals.py backend/tests/test_evidence.py backend/tests/test_guardrails.py
uv run pytest backend/tests
uv run python scripts/run_evals.py --dataset workflow_e2e_cases --strict
uv run python scripts/run_evals.py --dataset safety_guardrail_cases --strict
```

## Human Review Checklist

- [ ] Agent들이 하나의 거대 agent로 합쳐지지 않았는가?
- [ ] Aggregator가 새 판단을 임의로 만들지 않고 agent output만 병합하는가?
- [ ] 외부 발송/전달/제출은 여전히 approval pending인가?
- [ ] Evidence Log에 aggregator 실행 흔적이 남는가?
- [ ] 기존 API 소비자가 쓰던 `draft`, `tool_results`가 깨지지 않는가?
- [ ] final response가 사람이 검토하기 쉬운 하나의 case output을 제공하는가?
