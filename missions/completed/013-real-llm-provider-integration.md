# Mission 013: Real LLM Provider Integration

## Goal

검증된 fake judgment chain과 LangChain adapter 뒤에 실제 LLM provider를 feature flag 기반으로 연결한다.

기본값은 여전히 fake/deterministic이어야 하며, 명시적 env flag 없이는 실제 외부 LLM API를 호출하지 않는다.

---

## Required Reading

```txt
AGENTS.md
docs/ARCHITECTURE.md
docs/SECURITY_GUARDRAILS.md
docs/OBSERVABILITY.md
missions/active/009-llm-judgment-json-chain.md
missions/active/011-judgment-runtime-mode.md
missions/active/012-langchain-judgment-adapter.md
```

---

## Target Files

```txt
backend/app/config.py
backend/app/agent_runtime/llm/client.py
backend/app/agent_runtime/langchain_runtime/judgment_agent.py
backend/app/agent_runtime/graph/workflow.py
.env.example

backend/tests/test_llm_judgment_chain.py
backend/tests/test_agent_workflow.py
backend/tests/test_guardrails.py
backend/tests/test_pii_filter.py
```

---

## Scope

- real provider feature flag 추가
- fake client 기본값 유지
- timeout 처리
- invalid JSON 처리
- provider error 처리
- raw PII provider payload 차단
- LLM output parser와 guardrail 강제
- approval required action은 계속 pending 유지

---

## Out of Scope

- 비용 대시보드
- streaming UI
- fine-tuning
- prompt injection 고급 방어
- 자동 메시지 발송
- 정부 포털 제출
- 법률/노무 판단 확정

---

## Verification Commands

```bash
uv run pytest backend/tests/test_llm_judgment_chain.py backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py backend/tests/test_pii_filter.py
python scripts/run_evals.py --dataset safety_guardrail_cases --strict
python scripts/run_evals.py --dataset workflow_e2e_cases --strict
```

---

## Human Review Checklist

- [ ] feature flag 없이 실제 LLM 호출이 발생하지 않는가?
- [ ] raw PII가 provider payload에 들어가지 않는가?
- [ ] invalid JSON과 timeout이 blocked/error로 드러나는가?
- [ ] LLM 결과가 guardrail을 우회하지 않는가?
