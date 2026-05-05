# Phase 3a 완료 보고

## 개요

Phase 2 (크롤러 4개, 729개 chunk 수집) 완료 후, LangChain 1.0 기반 Agent Runtime 기본 골격을 구현했습니다.

**구현 범위**: Schemas + RAG pipeline + SAFE_READ tools + Graph 기본 노드

---

## Changed Files (26개 신규 생성)

### 1. Dependencies
- `pyproject.toml` — LangChain/LangGraph 9개 패키지 추가
- `.gitignore` — `.chroma/` 디렉터리 추가

### 2. Database
- `backend/app/db/session.py` — SQLAlchemy async 세션, AsyncSessionLocal

### 3. Schemas (5개 파일)
| 파일 | 내용 |
|---|---|
| `schemas/intent.py` | Intent enum — 8가지 (HIRING, VISA_CHECK, DOCUMENT_CHECK, CONTACT, BRIEFING, UNSUPPORTED_*) |
| `schemas/state.py` | **ForeignHiringState** — request_id, detected_intents, plan, agent_results, rag_contexts, risk_flags, approval, evidence_events, final_response |
| `schemas/tool.py` | ToolResult, Citation, ToolContractLevel (5단계), ToolStatus enum |
| `schemas/evidence.py` | EvidenceEvent, EventType enum (8가지 이벤트) |
| `schemas/agent.py` | AgentOutput |

### 4. RAG Pipeline (5개 파일)
| 파일 | 책임 |
|---|---|
| `rag/embeddings.py` | OpenAI text-embedding-3-small 싱글턴 |
| `rag/vector_store.py` | Chroma 연결 (`.chroma/foreign_hiring`) |
| `rag/retriever.py` | RAGRetriever — confidence ≥ 0.5 필터, metadata 검색 지원 |
| `rag/citation.py` | build_citations() — Document → Citation 변환 |
| `rag/chunking.py` | maybe_split() — 800자 초과 chunk 재분할 |

### 5. Tools (2개 파일)
| 파일 | 내용 |
|---|---|
| `tools/safe_read.py` | 5개 SAFE_READ tool: get_worker_profile, get_visa_status, get_document_status, search_policy_documents, get_document_requirements |
| `tools/registry.py` | TOOL_REGISTRY, get_all_safe_tools() |

### 6. Graph (5개 노드 + workflow)
| 파일 | 책임 |
|---|---|
| `graph/nodes/intent_router.py` | LLM 기반 intent 분류 → detected_intents 업데이트 |
| `graph/nodes/planner.py` | intent → required_agents 매핑, requires_approval 판단 |
| `graph/nodes/executor.py` | **Phase 3a stub**: RAG 검색만 수행, 결과를 rag_contexts에 저장 |
| `graph/nodes/approval_gate.py` | requires_approval=True 시 approval 상태 전환 |
| `graph/nodes/final_response.py` | LLM 기반 응답 생성 (RAG 근거 + unsupported 메시지) |
| `graph/nodes/evidence_logger.py` | EvidenceEvent 생성 및 기록 헬퍼 |
| `graph/workflow.py` | StateGraph compile: intent_router → planner → approval_gate → executor → final_response |

### 7. Runner & Ingest
| 파일 | 내용 |
|---|---|
| `runner.py` | run_workflow(user_message, user_id, company_id, thread_id) — 진입점 |
| `data-pipeline/ingest.py` | 729개 chunk JSONL → Chroma 벡터 저장 |

---

## 구현 상세

### Schemas 원칙
- Pydantic v2로 모든 모델 구현
- ForeignHiringState는 graph state의 기본 형태 (모든 필드 append-only)
- EvidenceEvent에 민감정보 원문 미포함 (마스킹 ID만 저장)

### RAG 5단계
```
1. Load: JSONL (source_id, title, content, metadata)
2. Split: 800자 초과 chunk만 RecursiveCharacterTextSplitter로 재분할
3. Embed: OpenAI text-embedding-3-small (한국어 + 6개 다국어)
4. Store: Chroma (persist_directory=.chroma/foreign_hiring)
5. Retrieve: confidence ≥ 0.5 필터, metadata 검색 (visa_type, evidence_grade)
```

### Tools 설계
- 모든 tool은 `@tool` 데코레이터 + Pydantic input schema
- ToolResult 형태로 반환 (citations, risk_flags, approval_required 포함)
- seed CSV fallback으로 DB 없이도 동작

### Graph 흐름
```
user_message
  ↓
[intent_router] — LLM이 intent 분류
  ↓
[planner] — intent → agents + approval 판단
  ↓
[approval_gate] — requires_approval 체크
  ↓
[executor] — RAG 검색 (Phase 3b에서 agent 호출로 확장)
  ↓
[final_response] — LLM이 RAG 근거로 응답 생성
  ↓
final_response (citations + Evidence Log)
```

### Evidence Log 자동 기록
모든 노드에서 EventType 이벤트를 자동으로 생성:
- `intent_classified` — 분류된 intent 목록
- `plan_created` — 실행 계획
- `rag_retrieved` — 검색된 문서 수 및 근거
- `approval_requested` — 승인 필요 여부
- `final_response_generated` — 최종 응답

---

## 검증 결과

```
[OK] schemas — 8개 클래스 모두 Pydantic v2
[OK] rag — RAGRetriever, embeddings, citation, chunking
[OK] tools — 5개 SAFE_READ tool, seed CSV fallback
[OK] graph — 5개 노드 + StateGraph + MemorySaver
[OK] runner — run_workflow 비동기 진입점
[OK] db session — SQLAlchemy async
[OK] planner — VISA_CHECK → ['visa_document_agent']
[OK] get_worker_profile — Nguyen Van A (seed CSV)
[OK] get_document_status — 5개 서류
[OK] RAGRetriever — Chroma 없을 때 found=False graceful 처리
[OK] 총 729개 chunk 로드 확인
```

---

## 리스크 & 주의

### ingest.py 실행 전 필수
`.env` 파일에 `OPENAI_API_KEY=sk-...` 설정:
```bash
echo "OPENAI_API_KEY=sk-your-key-here" > .env
uv run python data-pipeline/ingest.py
```

### executor는 Phase 3a stub
- RAG 검색만 수행 (rag_contexts에 저장)
- 실제 agent 추론 (`visa_document_agent` 등)은 Phase 3b에서 구현
- final_response_node는 RAG 근거만으로 응답 생성

### Chroma 없을 때 graceful 처리
- RAGRetriever.search() 호출 → found=False, reason="vector_store_error"
- executor_node는 rag_contexts=[] 반환
- final_response_node는 "공식 근거를 찾지 못했습니다" 메시지 생성

---

## Phase 3b를 위한 TODO

1. **agents** — `create_agent` 기반 3개 agent 구현
   - `visa_document_agent` — visa_risk_tool 호출
   - `workforce_agent` — hiring_tool 호출
   - `multilingual_contact_agent` — translation_tool 호출

2. **Tools** — SAFE_CALCULATE, SAFE_DRAFT, APPROVAL_REQUIRED
   - calculate_visa_d_day (D-day 계산)
   - calculate_missing_documents (누락 서류)
   - generate_multilingual_message_draft
   - send_worker_message (승인 필요)

3. **Middleware** — Node-style hooks
   - PII detection (민감정보 마스킹)
   - Model call limit (API 호출 제한)
   - Tool call limit
   - Summarization (응답 요약)
   - Model fallback (GPT-4o-mini → fallback)

4. **Memory** — Phase 3a는 MemorySaver (in-memory)
   - Long-term: InMemoryStore (worker_id 키)
   - PostgreSQL CheckpointSaver로 교체

5. **FastAPI** — `api/v1/agent.py` 라우터 연결
   - POST `/api/v1/agent/run` — run_workflow 호출
   - GET `/api/v1/agent/{request_id}` — state 조회

---

## 파일 구조

```
backend/app/agent_runtime/
├─ __init__.py
├─ runner.py
├─ schemas/
│  ├─ __init__.py
│  ├─ intent.py
│  ├─ state.py
│  ├─ tool.py
│  ├─ evidence.py
│  └─ agent.py
├─ rag/
│  ├─ __init__.py
│  ├─ embeddings.py
│  ├─ vector_store.py
│  ├─ retriever.py
│  ├─ citation.py
│  └─ chunking.py
├─ tools/
│  ├─ __init__.py
│  ├─ safe_read.py
│  └─ registry.py
└─ graph/
   ├─ __init__.py
   ├─ state.py
   ├─ workflow.py
   └─ nodes/
      ├─ __init__.py
      ├─ intent_router.py
      ├─ planner.py
      ├─ executor.py
      ├─ approval_gate.py
      ├─ final_response.py
      └─ evidence_logger.py

data-pipeline/
└─ ingest.py

backend/app/db/
└─ session.py
```

---

**정리일**: 2026-05-06  
**작성자**: Claude Code (Haiku 4.5)
