# Mission 008: RAG Evidence Package

## Goal

검색 결과를 LLM 판단 체인에 넣을 수 있는 표준 Evidence Package JSON으로 고정한다.

현재 RAG는 chunk 검색과 retrieval eval까지 가능하지만, LLM 입력 계약이 없다. 이 mission은 검색 결과를 `request_id`, `query`, `case_type`, `retrieved_chunks`, `citations`, `missing_evidence`, `evidence_policy`를 가진 안전한 입력 패키지로 만드는 것이 목적이다.

---

## Required Reading

```txt
AGENTS.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/RAG_STRATEGY.md
docs/TOOL_CONTRACT.md
docs/SECURITY_GUARDRAILS.md
docs/EVIDENCE_LOG_SCHEMA.md
docs/EVAL_HARNESS.md
missions/active/002-rag-indexing.md
missions/completed/001-agent-runtime-skeleton.md
```

---

## Target Files

```txt
backend/app/agent_runtime/rag/retriever.py
backend/app/agent_runtime/rag/citation.py
backend/app/agent_runtime/rag/evidence_package.py

backend/app/agent_runtime/schemas/evidence.py

backend/tests/test_rag_indexing.py
backend/tests/test_evidence_package.py

evals/datasets/rag_retrieval_cases.jsonl
```

---

## Scope

이번 mission에서 구현할 범위는 다음과 같다.

- Evidence Package schema 정의
- `request_id`, `query`, `case_type`, `retrieved_chunks`, `citations`, `missing_evidence`, `evidence_policy` 필드 고정
- RAG 검색 결과를 Evidence Package로 변환하는 builder 추가
- 답변 근거로 사용할 수 있는 evidence grade를 A/B/E로 제한
- F grade synthetic/demo data를 공식 판단 근거에서 제외
- 검색 결과가 없거나 필수 metadata가 없으면 silent fallback 금지
- `status=ready`, `status=insufficient_evidence`, `status=blocked` 상태 구분
- RAG eval case 기준 Evidence Package 생성 테스트 추가

---

## Out of Scope

이번 mission에서 구현하지 않는다.

- 실제 LLM 호출
- Prompt template 작성
- LLM 출력 JSON parser
- 위험도 분류
- 사용자용 리포트 생성
- 새로운 공식 문서 수집
- 고급 reranker 또는 외부 embedding API 연동

---

## Evidence Package Contract

```json
{
  "status": "ready",
  "request_id": "req_001",
  "query": "E-9 신규 채용 절차 근거 찾아줘",
  "case_type": "new_hiring",
  "retrieved_chunks": [
    {
      "chunk_id": "seed_eps_procedure_demo_001__0001",
      "source_id": "seed_eps_procedure_demo_001",
      "title": "E-9 고용허가 절차 데모 문서",
      "text": "내국인 구인노력 후 고용허가 신청을 준비한다.",
      "evidence_grade": "B",
      "doc_type": "procedure",
      "citation": "[E-9 고용허가 절차 데모 문서, MVP seed placeholder]"
    }
  ],
  "citations": [
    {
      "source_id": "seed_eps_procedure_demo_001",
      "chunk_id": "seed_eps_procedure_demo_001__0001",
      "citation": "[E-9 고용허가 절차 데모 문서, MVP seed placeholder]"
    }
  ],
  "missing_evidence": [],
  "evidence_policy": {
    "answer_evidence_grades": ["A", "B", "E"],
    "excluded_grades": ["C", "D", "F"],
    "synthetic_official_claims_allowed": false
  }
}
```

---

## Acceptance Criteria

- Evidence Package builder가 존재한다.
- package에는 `request_id`, `query`, `case_type`, `retrieved_chunks`, `citations`, `missing_evidence`, `evidence_policy`가 포함된다.
- 답변 근거에는 A/B/E grade만 포함된다.
- F grade synthetic/demo data는 공식 판단 근거로 쓰이지 않는다.
- 검색 결과가 없으면 fallback text를 만들지 않고 `insufficient_evidence`로 표시한다.
- metadata 누락은 silent fallback 대신 명시적 error 또는 blocked 상태로 처리된다.
- `rag_retrieval_cases.jsonl` 기반 package 생성 테스트가 통과한다.

---

## Verification Commands

```bash
uv run pytest backend/tests/test_evidence_package.py backend/tests/test_rag_indexing.py backend/tests/test_rag_eval_dataset.py
python scripts/run_evals.py --dataset rag_retrieval_cases --strict
```

---

## Human Review Checklist

- [ ] LLM 입력으로 넘길 evidence package 계약이 명확한가?
- [ ] A/B/E 외 evidence가 공식 판단 근거로 들어가지 않는가?
- [ ] synthetic/demo data가 공식 claim 근거로 오용되지 않는가?
- [ ] 빈 검색 결과가 안전하게 드러나는가?
- [ ] source_id와 chunk_id가 누락되지 않는가?
