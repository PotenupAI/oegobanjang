# Evidence Log 스키마

## 1. 목적

Evidence Log는 AI가 왜 그렇게 판단했는지, 어떤 근거를 사용했는지, 누가 승인했는지를 추적하기 위한 기록이다.

외고반장은 법적 리스크와 행정 사고를 다루므로, 모든 중요한 판단은 설명 가능해야 한다.

---

## 2. 저장해야 하는 이벤트

- intent_classified
- plan_created
- tool_executed
- rag_retrieved
- risk_flagged
- approval_requested
- approval_completed
- final_response_generated

---

## 3. `evidence_logs` 테이블 초안

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | UUID | 로그 ID |
| timestamp | timestamp | 이벤트 발생 시각 |
| work_item_id | varchar | work item, fixture, case ID |
| request_id | UUID | 사용자 요청 ID |
| company_id | UUID | 사업장 ID |
| worker_id | UUID nullable | 근로자 ID |
| agent_id | varchar | 실행 Agent ID |
| agent_name | varchar | 실행 Agent |
| step_name | varchar | 실행 단계 |
| event_type | varchar | 이벤트 유형 |
| action_type | varchar | `retrieve` / `judge` / `approve` / `handoff` 등 표준 action |
| tool_name | varchar nullable | 실행 Tool |
| input_snapshot | jsonb | 입력 스냅샷 |
| output_snapshot | jsonb | 출력 스냅샷 |
| confidence | numeric nullable | 라우팅/판단 confidence. 법적 확실성 점수가 아님 |
| human_override | boolean | 사람이 AI 출력을 수정/override 했는지 여부 |
| citation_ids | jsonb | 참조 문서 ID |
| evidence_chunk_ids | jsonb | RAG 근거 chunk ID |
| risk_level | varchar | LOW/MEDIUM/HIGH |
| approval_id | UUID nullable | 승인 ID |
| created_at | timestamp | 생성 시각 |

---

## 4. 표준 이벤트 JSON

Phase 3의 audit log는 append-only event source로 취급한다. 모든 Agent, Tool, RAG, Approval 단계는 아래 공통 필드를 기준으로 이벤트를 남긴다.

```json
{
  "timestamp": "2026-05-04T10:08:02Z",
  "work_item_id": "case_003",
  "agent_id": "workforce_agent",
  "action_type": "retrieve",
  "input": {},
  "output": {},
  "confidence": 0.85,
  "human_override": false,
  "evidence_chunk_ids": ["chunk_id_xxx"]
}
```

### `action_type`

```txt
retrieve
judge
approve
handoff
route
plan
execute_tool
block
```

- `retrieve`: RAG 또는 SAFE_READ 조회.
- `judge`: deterministic 또는 LLM-assisted 분류, risk flagging, document-gap 판단.
- `approve`: 사람 승인 요청, 완료, 거절, override.
- `handoff`: 승인 이후 handoff package 준비. 외부 전달을 의미하지 않는다.
- `route`: intent 또는 case routing.
- `plan`: workflow plan 생성.
- `execute_tool`: tool 실행 결과.
- `block`: Stop Condition 또는 금지 요청.

---

## 5. Event Source 원칙

- Audit event는 INSERT-only로 기록한다. 기존 event를 UPDATE하지 않는다.
- 하나의 `work_item_id`에 대한 event replay만으로 state reconstruction이 가능해야 한다.
- 중복 transition event는 아래 transition key로 idempotent하게 처리한다.
  `(work_item_id, current_state, next_state, action_type)`.
- metadata가 누락됐을 때 silent fallback을 사용하지 않는다. 명시적인 reason과 함께 `action_type="block"` event를 남긴다.
- `input`과 `output`은 snapshot이다. raw production document를 저장하지 않는다.

---

## 6. 민감정보 처리

Evidence Log에는 다음 원문을 저장하지 않는다.

- 외국인등록번호
- 여권번호
- 전화번호 전체
- 주소 전체
- 서류 파일 원문

저장 가능한 정보:

- 마스킹된 식별자
- 문서 보유 여부
- source_id
- 판단 요약
- 승인 상태
- 처리 시각

---

## 7. 예시

```json
{
  "timestamp": "2026-05-04T10:08:02Z",
  "work_item_id": "case_003",
  "event_type": "risk_flagged",
  "request_id": "req_001",
  "agent_id": "visa_document_agent",
  "agent_name": "visa_document_agent",
  "step_name": "visa_risk_check",
  "action_type": "judge",
  "summary": "체류만료 D-30 구간으로 관리자 확인이 필요합니다.",
  "citation_ids": ["gov24_stay_extension"],
  "evidence_chunk_ids": ["gov24_stay_extension__0001"],
  "risk_level": "MEDIUM",
  "confidence": 0.85,
  "human_override": false,
  "approval_id": null
}
```
