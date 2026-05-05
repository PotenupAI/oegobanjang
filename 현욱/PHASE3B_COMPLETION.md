# Phase 3b 완료 보고

## 개요

Phase 3a (기본 골격) 완료 후, 실제 동작하는 **3개 agent + 전체 tools + middleware + FastAPI 라우터**를 구현했습니다.

---

## Changed Files

### 1. Tools 확장

| 파일 | 등급 | 구현된 tool |
|---|---|---|
| `tools/safe_calculate.py` | SAFE_CALCULATE | `calculate_visa_d_day`, `calculate_missing_documents`, `calculate_contract_gap` |
| `tools/safe_draft.py` | SAFE_DRAFT | `generate_multilingual_message_draft`, `generate_expert_handoff_package_draft` |
| `tools/approval_required.py` | APPROVAL_REQUIRED | `send_worker_message`, `send_expert_package`, `update_case_status_completed` |
| `tools/registry.py` | — | 전체 TOOL_REGISTRY 업데이트 (10개 safe + 3개 approval) |

**전체 tool 수**: 10개 safe tools (READ 5 + CALCULATE 3 + DRAFT 2) + 3개 approval tools

### 2. Middleware (신규)

| 파일 | 기능 |
|---|---|
| `middleware/pii_filter.py` | 여권번호, 외국인등록번호, 전화번호 마스킹 (`mask_pii`, `sanitize_dict`) |
| `middleware/call_limiter.py` | LLM 10회 / tool 20회 세션 제한 (`check_llm_limit`, `check_tool_limit`) |
| `middleware/summarizer.py` | rag_contexts 3000자 초과 시 LLM 자동 요약 (`maybe_summarize_contexts`) |

### 3. Agents (3개 구현)

| 파일 | Agent | 사용 tools |
|---|---|---|
| `agents/visa_agent.py` | visa_document_agent | get_worker_profile, get_visa_status, get_document_status, search_policy_documents, calculate_visa_d_day, calculate_missing_documents, calculate_contract_gap, generate_expert_handoff_package_draft |
| `agents/hiring_agent.py` | workforce_agent | get_worker_profile, search_policy_documents, get_document_requirements, generate_expert_handoff_package_draft |
| `agents/contact_agent.py` | multilingual_contact_agent | get_worker_profile, search_policy_documents, generate_multilingual_message_draft, send_worker_message(승인필요) |

### 4. Executor 업그레이드

`graph/nodes/executor.py`:
- Phase 3a stub → RAG 검색 + 실제 agent 호출로 전환
- required_agents 순서대로 visa_agent / hiring_agent / contact_agent 실행
- `maybe_summarize_contexts()` 적용 (컨텍스트 초과 방지)
- 고위험 플래그 감지 시 `risk_flagged` 이벤트 기록

### 5. final_response 업그레이드

`graph/nodes/final_response.py`:
- agent_results 요약 포함
- risk_flags 강조 표시
- PII 마스킹 (`mask_pii`) 응답에 자동 적용

### 6. FastAPI 라우터 연결

| 파일 | 변경 |
|---|---|
| `api/v1/agent.py` | `POST /api/v1/agent/run`, `GET /api/v1/agent/state/{request_id}` |
| `api/v1/router.py` | agent 라우터 등록 |
| `main.py` | `api_v1_router` include |

---

## 전체 Tool 구조

```
SAFE_READ (5개):
  get_worker_profile, get_visa_status, get_document_status,
  search_policy_documents, get_document_requirements

SAFE_CALCULATE (3개):
  calculate_visa_d_day      → D-day 계산 + risk_level (LOW/MEDIUM/HIGH)
  calculate_missing_documents → 케이스별 누락 서류 목록
  calculate_contract_gap    → 비자↔계약 기간 gap 계산

SAFE_DRAFT (2개):
  generate_multilingual_message_draft   → 6개 언어 메시지 초안
  generate_expert_handoff_package_draft → 행정사 전달 패키지 초안

APPROVAL_REQUIRED (3개):  ← 항상 NEEDS_APPROVAL 반환
  send_worker_message       → 근로자 SMS/카카오 발송
  send_expert_package       → 행정사/노무사 패키지 전달
  update_case_status_completed → 케이스 완료 처리
```

---

## Middleware 동작 방식

### PII Filter
```python
mask_pii("여권번호 M12345678 전화번호 010-1234-5678")
# → "여권번호 [여권번호] 전화번호 [전화번호]"
```

마스킹 대상:
- 외국인등록번호: `\d{6}-\d{7}` → `[외국인등록번호]`
- 여권번호: `[A-Z]{1,2}\d{7,8}` → `[여권번호]`
- 전화번호: `01X-XXXX-XXXX` 패턴 → `[전화번호]`

### Call Limiter
- LLM 호출: 세션(request_id)당 10회 제한
- Tool 호출: 세션당 20회 제한
- 초과 시 error 메시지 반환 (예외 발생 없음)

### Summarizer
- rag_contexts 총 글자수 > 3000자 시 자동 요약
- OPENAI_API_KEY 없으면 앞 500자로 잘라서 반환 (fallback)

---

## Agent 흐름

```
executor_node
  ↓ RAG 검색 + summarizer 적용
  ↓ required_agents 순서 실행
    visa_document_agent
      ├─ call_limiter 체크
      ├─ LLM + bind_tools 호출
      ├─ tool_calls 실행 (calculate_visa_d_day 등)
      ├─ risk_flags 수집
      └─ TOOL_EXECUTED 이벤트 기록
    workforce_agent (HIRING intent)
    multilingual_contact_agent (CONTACT intent)
      └─ send_worker_message 호출 → NEEDS_APPROVAL
         → state.approval = PENDING
         → APPROVAL_REQUESTED 이벤트 기록
  ↓
final_response_node
  ├─ agent_results + rag_contexts + risk_flags 통합
  ├─ LLM 응답 생성 (Grade A > B > C > D 인용)
  └─ mask_pii() 적용 후 반환
```

---

## 검증 결과

```
[OK] SAFE_CALCULATE: 3개
[OK] SAFE_DRAFT: 2개
[OK] APPROVAL_REQUIRED: 3개
[OK] 전체 safe tools: 10개
[OK] middleware: pii_filter, call_limiter, summarizer
[OK] agents: visa, hiring, contact
[OK] FastAPI: routes 8개
[OK] calculate_visa_d_day: D-4, risk=HIGH  ← seed 데이터 기준 체류만료 D-4
[OK] calculate_missing_documents: 누락 1건 (work_permit), 보유 4건
[OK] calculate_contract_gap: gap=387일 (계약이 비자보다 387일 김)
[OK] generate_multilingual_message_draft(베트남어): 비자 만료 알림 초안
[OK] send_worker_message: NEEDS_APPROVAL — 발송 차단 확인
[OK] PII 마스킹: 여권번호/전화번호 자동 마스킹
[OK] call_limiter: 정상 동작
[OK] agent 라우터: /api/v1/agent/run, /api/v1/agent/state/{request_id}
```

---

## API 사용법

### POST /api/v1/agent/run
```json
{
  "user_message": "E-9 근로자 체류연장에 필요한 서류 알려줘",
  "user_id": "user_001",
  "company_id": "company_001",
  "thread_id": null
}
```

응답:
```json
{
  "request_id": "...",
  "final_response": "[출입국관리법 시행규칙] 체류연장 필요 서류...",
  "detected_intents": ["VISA_CHECK"],
  "risk_flags": [],
  "approval_required": false,
  "approval_status": "NOT_REQUIRED",
  "evidence_event_count": 4,
  "rag_context_count": 5
}
```

---

## Phase 3c를 위한 TODO

1. **Eval harness** — 5개 데이터셋 기반 자동 평가
   - `safety_guardrail_cases.jsonl` — FORBIDDEN intent 차단 확인
   - `document_gap_cases.jsonl` — 누락 서류 계산 정확도
   - `visa_d_day_cases.jsonl` — D-day 계산 + risk_level 정확도
   - `multilingual_cases.jsonl` — 6개 언어 메시지 생성 확인
   - `evidence_grade_cases.jsonl` — Grade A > B > C > D 우선순위 준수

2. **PostgreSQL CheckpointSaver** — MemorySaver → DB 교체 (프로세스 재시작 후도 유지)

3. **InMemoryStore** — worker_id 키 기반 장기 메모리

---

**정리일**: 2026-05-06  
**작성자**: Claude Code (Sonnet 4.6)
