# Mission 011: Judgment Runtime Mode

## Goal

기존 deterministic WorkBridge runtime을 유지하면서 `runtime_mode="langchain_judgment"`일 때만 판단 리포트 노드를 선택적으로 실행한다.

LangChain 또는 실제 LLM provider를 직접 연결하지 않는다. 이 mission은 Mission 009/010에서 검증된 fake/provider-agnostic judgment chain과 report generator를 workflow에 안전하게 끼우는 것이 목적이다.

---

## Required Reading

```txt
AGENTS.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/AI_OS_DESIGN.md
docs/SECURITY_GUARDRAILS.md
docs/EVIDENCE_LOG_SCHEMA.md
missions/active/009-llm-judgment-json-chain.md
missions/active/010-risk-report-generation.md
missions/completed/001-agent-runtime-skeleton.md
```

---

## Target Files

```txt
backend/app/schemas/agent.py
backend/app/agent_runtime/graph/workflow.py
backend/app/agent_runtime/graph/nodes/final_response.py
backend/app/agent_runtime/graph/nodes/evidence_logger.py

backend/tests/test_agent_workflow.py
backend/tests/test_guardrails.py
backend/tests/test_evidence.py
```

---

## Scope

- `AgentRunRequest.runtime_mode` 추가
- 허용 값: `deterministic`, `langchain_judgment`
- 기본값: `deterministic`
- 기존 `/api/v1/agent/run` endpoint 유지
- 기존 deterministic workflow 결과 보존
- `approval_gate` 이후, `final_response` 이전에 optional judgment node 실행
- unsupported/blocked request에서는 judgment node 미호출
- judgment/report 결과를 `final_response`와 Evidence Log 후보 이벤트에 포함

---

## Out of Scope

- LangChain import
- OpenAI 또는 외부 LLM 호출
- Chroma persistent index 생성
- 실제 provider timeout/error 처리
- 메시지 발송, 정부 포털 제출, 외부 export

---

## Runtime Flow

```txt
mask_payload
-> route_intent
-> guardrail pre-check
-> create_plan
-> execute_plan
-> approval_gate
-> if runtime_mode == "langchain_judgment" and not blocked: judgment node
-> evidence append
-> final_response
-> final guardrail check
```

---

## Acceptance Criteria

- `runtime_mode` 기본값은 `deterministic`이다.
- 기존 request payload는 변경 없이 계속 동작한다.
- `runtime_mode="deterministic"`에서는 judgment report가 생성되지 않는다.
- `runtime_mode="langchain_judgment"`에서는 fake judgment/report가 생성된다.
- blocked/unsupported request에서는 judgment node가 호출되지 않는다.
- approval required request는 judgment 이후에도 `PENDING` 상태로 남는다.
- final guardrail check가 유지된다.

---

## Verification Commands

```bash
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py backend/tests/test_evidence.py
python scripts/run_evals.py --dataset safety_guardrail_cases --strict
python scripts/run_evals.py --dataset workflow_e2e_cases --strict
```

---

## Human Review Checklist

- [ ] 기존 deterministic 기본 동작이 깨지지 않았는가?
- [ ] LangChain 판단 모드는 명시적으로 요청할 때만 켜지는가?
- [ ] blocked request가 judgment node를 우회하는가?
- [ ] approval gate가 judgment node보다 먼저 실행되는가?
- [ ] final guardrail check가 유지되는가?
