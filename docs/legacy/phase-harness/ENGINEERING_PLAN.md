# 워크브리지 엔지니어링 계획 - 신뢰성 핵심 5

> Demo 수준에서 production-ready 수준으로 옮기는 가장 짧은 길이다.
> Product 측 안전 가드(Forbidden, human approval, evidence_grade)는 이미 들어가 있다.
> 이 문서는 그 다음 계층, 즉 *실패해도 안전하게 무너지는 방식*을 정리한다.

---

## 한 페이지 요약

```txt
PII 마스킹      → router 앞 middleware
Embedding cache → ingest pipeline 안
Idempotency    → state machine transition
Audit log      → INSERT-only event source
Failure mode   → 모든 phase Stop Conditions
```

---

## 핵심 5가지

### 1. PII 마스킹 - "주민등록번호를 가린 팩스"

| 항목 | 내용 |
|---|---|
| 무엇 | 외국인등록번호(13자리), 여권번호, 핸드폰 번호가 들어오면 `▲▲▲`로 가리고 처리하고, 출력 직전에만 복원한다 |
| 왜 1순위 | 외국인 노동자 도메인이라 사고 시 법적 책임이 크다. LLM이나 로그에 한 번 들어가면 회수할 수 없다 |
| 안 하면 | OpenAI 서버에 외국인등록번호를 보내 개인정보보호법을 위반할 수 있다 |
| 어디 | `src/middleware/pii_filter.py`. router에 들어가기 직전에 호출한다 |

**비유**: 팩스를 보낼 때 주민번호를 손으로 가리는 것과 같다. 보낼 때 가리고, 받은 사람만 복원해서 본다.

### 2. Embedding cache - "한 번 계산한 답 저장해두기"

| 항목 | 내용 |
|---|---|
| 무엇 | 같은 chunk를 두 번 임베딩하지 말고, 한 번 만든 vector를 SQLite에 저장한다 |
| 왜 2순위 | Phase 1C에서 chunk 30개 이상을 매번 새로 호출하면 비용과 시간이 낭비된다. ingest를 다시 돌릴 때마다 5분씩 더 든다 |
| 안 하면 | 개발 중 OpenAI 호출이 폭주해 청구서가 커질 수 있다 |
| 어디 | `data/cache/embeddings.sqlite`. 키 = `sha256(chunk_text)`, 값 = vector |

**비유**: 곱셈표를 외워두는 것과 같다. 7×8을 매번 계산하지 말고 56을 기억해 둔다.

### 3. Idempotency in state machine - "같은 요청이 두 번 와도 같은 결과"

| 항목 | 내용 |
|---|---|
| 무엇 | 같은 case_id가 두 번 들어와도 case가 두 번 만들어지지 않게 한다 |
| 왜 3순위 | 사용자가 새로고침을 누르거나 네트워크가 끊겼다 재전송하면 중복 생성이 생긴다. Phase 3의 핵심이다 |
| 안 하면 | 같은 회사가 두 번 표시되거나, evidence가 중복 인용되거나, 행정사 패키지가 두 번 생길 수 있다 |
| 어디 | `src/workflow_state.py`에서 transition을 만들 때 `(case_id, from_state, to_state)` 키로 중복 제거한다 |

**비유**: 엘리베이터 버튼을 두 번 눌러도 한 번만 작동한다. transition 키로 이미 처리한 요청인지 먼저 확인한다.

### 4. Audit log를 event source로 - "행정사 사후 질문에 답할 수 있게"

| 항목 | 내용 |
|---|---|
| 무엇 | 모든 state 변경을 시간순으로 영속(SQLite)한다. UPDATE 없이 INSERT만 사용한다 |
| 왜 4순위 | 행정사가 "왜 이 결정을 내렸나"를 물으면 evidence trail이 있어야 답할 수 있다. 단순 로그와 event source는 다르다 |
| 안 하면 | 데모는 통과해도 실제 사용자(행정사)가 신뢰하지 못한다 |
| 어디 | `data/state.db`의 `audit_logs(id, case_id, action, evidence_chunk_ids, actor, timestamp)` |

**비유**: 의료 차트와 같다. UPDATE를 하지 않고 새 항목만 추가한다. 어떤 시점에 무엇이 결정됐는지 시간순으로 모두 남는다.

### 5. Failure mode 명시 - "실패해도 안전하게 무너지기"

| 항목 | 내용 |
|---|---|
| 무엇 | retrieval 0건, embedding 실패, chunk 메타 누락을 silently fallback하지 말고 `status: blocked` 또는 `error`로 처리한다 |
| 왜 5순위 | `sources.json`의 `case_type=ALL` 문제처럼 silent fallback이 가장 위험하다 |
| 안 하면 | 겉보기에는 통과하지만 내실은 망가진 상태가 누적된다. Phase 1에서 1C로 오며 이미 한 번 겪은 문제다 |
| 어디 | 각 phase의 Stop Conditions에 한 줄씩 넣는다 |

**비유**: 정전 시 비상등이 켜져야 한다. 그냥 어두워지면 사람이 다친다. 실패가 눈에 보여야 한다.

---

## 실패 케이스별 처리 참고

| 실패 케이스 | 현재 상태 | 권장 처리 |
|---|---|---|
| retrieval 0건 | 내부 동작이 모호하다 | `status: blocked` + "근거 없음" 응답 |
| embedding 실패 | retry가 없다 | retry queue + dead-letter |
| chunk 메타 누락 | silently ALL로 fallback한다 | 명시적 error |
| PII 감지됨 | 처리 없음 | log 마스킹 + audit_logs 기록 |

---

## 2단계 - 나중에 봐도 되는 항목

| 항목 | 도입 시점 |
|---|---|
| Citation 검증 (LLM이 인용한 chunk_id가 실제 존재하는지) | Phase 5+에서 LLM 도입 후 |
| Prompt injection 검사 | Phase 5+에서 LLM 도입 후 |
| Deterministic seed (`temperature=0` + seed 고정) | Phase 5+에서 LLM 도입 후 |
| Schema evolution ADR | 6개월 후 chunk_type이 늘어날 때 |
| Hit@3 drift CI | 운영 시작 시 |
| Approval rate dashboard | 운영 시작 시 |
| Risk flag 분포 모니터링 | 운영 시작 시 |

---

## 적용 순서

### 단계 1 - Phase 1C에 embedding cache 끼워넣기 완료

`phases/mvp/phase1c-chunk-and-embedding.md`에 이미 다음이 반영돼 있다:

- Allowed Writes: `src/cache/embedding_cache.py`, `data/cache/embeddings.sqlite`
- Step 3a: Embedding cache 구현 (`sha256` key, sqlite 저장)

→ Phase 1C 실행 시 자동으로 #2가 적용된다.

### 단계 2 - Phase 1C가 끝난 직후 PII filter를 phase로 분리

새 파일 `phases/mvp/phase2a-pii-middleware.md`:

```markdown
# 2A단계: PII 필터 미들웨어

## 목표
외국인등록번호, 여권번호, 핸드폰 번호를 router/LLM 호출 전에 마스킹한다.

## 입력
- 01_workforce_agent_schema.md
- src/workforce_router.py

## 허용 쓰기
- src/middleware/pii_filter.py
- tests/test_pii_filter.py

## 금지
- raw PII를 어디에도 저장하지 않는다.
- raw PII를 retrieve.py나 어떤 LLM에도 전달하지 않는다.
- raw PII를 로그에 남기지 않는다.

## 단계
1. PII regex 패턴을 정의한다.
2. `mask(text) -> masked_text + restore_map`를 구현한다.
3. `restore(text, map) -> original`을 구현한다. 이 함수는 output rendering에만 사용한다.
4. 외국인등록번호 13자리 → `▲▲▲▲▲▲-▲▲▲▲▲▲▲` 마스킹 테스트를 추가한다.

## 검증
```bash
uv run pytest tests/test_pii_filter.py
```

## 중단 조건
- 어떤 경로도 raw PII를 stdout, log, LLM에 흘리면 안 된다.
- PII 감지에 대해 silent fallback을 하면 안 된다. 명시적 reason과 함께 blocked로 표시한다.
```

→ Phase 2 router 앞에 middleware를 적용한다. **30분 작업.**

### 단계 3 - Phase 3 시작 전 Idempotency + Audit log를 v2 spec에 넣기

`phases/mvp/phase3-state-machine.md` v2에 추가:

```markdown
## 허용 쓰기 (추가)
- data/state.db (audit_logs table)

## 단계 (추가)
4. Implement idempotency:
   - transition key = (case_id, from_state, to_state)
   - duplicate transition → return existing result, do not create new

5. Implement audit_logs as event source:
   - INSERT only (no UPDATE)
   - schema: id, case_id, action, evidence_chunk_ids, actor, timestamp
   - state can be reconstructed by replaying audit_logs

## 중단 조건 (추가)
- A duplicate transition creates a new row → blocked.
- audit_logs UPDATE is attempted → error.
```

→ Phase 3 작업에 자연스럽게 포함된다.

### 단계 4 - 지금부터 일관되게 Failure mode 한 줄 추가

각 phase 파일의 Stop Conditions 마지막에 아래 줄을 추가한다:

```markdown
- Silent fallback on missing metadata or empty result is forbidden.
  Mark blocked with explicit reason instead.
```

→ 6개 phase 파일에 일괄 패치한다. **10분 작업.**

---

## 단계별 한 줄 요약

| Phase | 추가 항목 |
|---|---|
| 1C | ✅ Embedding cache (`data/cache/embeddings.sqlite`) - 적용됨 |
| 2A (신규) | PII filter middleware - Phase 1C 이후 |
| 2 (기존) | Audit middleware (라우팅 결정 + matched_terms 영속) - 선택 |
| 3 | Idempotency key (`case_id + phase + transition`) |
| 3 | Event-sourced `audit_logs` (state 복원 가능) |
| 4 | Evidence pinning (chunk_id에 ingest hash 첨부) |
| 4 | Approval token signing (위변조 방지) |

---

## 의사결정 기록 후보

이 문서의 결정 사항은 다음 ADR 후보로 넣을 수 있다:

- **ADR-003**: Retrieval reproducibility를 위해 embedding cache와 chunk version pinning을 사용한다.
- **ADR-004**: state machine 재구성과 행정사 handoff를 위해 event-sourced `audit_logs`를 사용한다.
- **ADR-005**: 어떤 외부 호출(router, retrieve, LLM)보다도 먼저 PII masking을 강제한다.
- **ADR-006**: 모든 phase에서 silent fallback을 금지한다. 실패는 `blocked` 또는 `error`로 드러나야 한다.

---

## 한 줄 결론

Product 측에서 잘한 것: *무엇을 자동화하지 않을 것인가*를 정해 둔 점이다.
엔지니어 측 다음 계층: *무엇이 실패할 때 어떻게 안전하게 무너질 것인가*를 정하는 것이다.

**Middleware (PII·gate) + Idempotency + Audit log + Failure mode + Observability** - 이 다섯 가지가 demo에서 production-ready로 가는 가장 짧은 길이다.
