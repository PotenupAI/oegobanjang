# Mission 012: LangChain Judgment Adapter

## Goal

Mission 009~011의 판단 계약을 유지하면서 LangChain 1.0 adapter를 선택형 구현으로 추가한다.

LangChain은 라우팅, 차단, 승인 판단의 최종권을 갖지 않는다. LangChain은 RAG 근거 검색, safe tool 호출, structured output 리포트 생성까지만 담당한다.

---

## Required Reading

```txt
AGENTS.md
docs/ARCHITECTURE.md
docs/RAG_STRATEGY.md
docs/SECURITY_GUARDRAILS.md
missions/active/009-llm-judgment-json-chain.md
missions/active/010-risk-report-generation.md
missions/active/011-judgment-runtime-mode.md
```

---

## Target Files

```txt
backend/app/agent_runtime/langchain_runtime/schemas.py
backend/app/agent_runtime/langchain_runtime/documents.py
backend/app/agent_runtime/langchain_runtime/vectorstore.py
backend/app/agent_runtime/langchain_runtime/tools.py
backend/app/agent_runtime/langchain_runtime/judgment_agent.py
scripts/build_langchain_rag_index.py

backend/tests/test_langchain_documents.py
backend/tests/test_langchain_judgment.py
evals/datasets/langchain_judgment_cases.jsonl
```

---

## Scope

- 기존 `data-pipeline/processed/chunks/all_chunks.jsonl` 재사용
- LangChain Document 변환
- Chroma persistent index builder 추가
- metadata `source_id`, `title`, `publisher`, `evidence_grade`, `chunk_type` 보존
- safe tool만 등록
- `retrieve_policy_context`
- `assess_readiness`
- fake LangChain runner로 테스트

---

## Forbidden Tools

```txt
send_worker_message
government_portal_submit
complete_case
external_export
destructive_db_update
```

---

## Out of Scope

- 기존 WorkBridge workflow 전면 교체
- deterministic router 대체
- approval gate 대체
- 실제 외부 발송/제출/export

---

## Verification Commands

```bash
uv run pytest backend/tests/test_langchain_documents.py backend/tests/test_langchain_judgment.py
python scripts/run_evals.py --dataset langchain_judgment_cases --strict
```

---

## Human Review Checklist

- [ ] LangChain이 safe tool만 사용할 수 있는가?
- [ ] 기존 metadata가 보존되는가?
- [ ] deterministic router/guardrail/approval을 대체하지 않는가?
- [ ] 테스트에서 OpenAI API를 호출하지 않는가?
