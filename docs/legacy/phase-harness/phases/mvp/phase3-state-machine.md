# 3단계: 워크플로우 상태 머신

## 목표
request preparation, explicit slot assembly, evidence retrieval, risk flag, human approval을 위한 단순한 workflow state machine을 만든다.

## 입력
- `01_workforce_agent_schema.md`
- `docs/DATA_GUIDE.md`
- `src/workforce_router.py`
- `src/retrieve.py`

## 허용 쓰기
- `src/case_factory.py`
- `src/workflow_state.py`
- `data/state.db`
- `tests/test_case_factory.py`
- `tests/test_workflow_state.py`

## 금지
- 외부 메시지를 보내지 않는다.
- government 또는 EPS API integration을 만들지 않는다.
- 요청을 auto-approve하지 않는다.
- 공식 EPS score를 계산하지 않는다.

## 단계
1. 허용된 workflow state와 transition을 테스트한다.
2. `company_id`, `headcount` 같은 explicit field를 바탕으로 deterministic case input assembly를 구현한다.
3. draft, evidence_ready, risk_review, human_approved, blocked에 대한 transition을 구현한다.
4. 어떤 external action state보다도 먼저 human approval을 요구한다.
5. idempotency를 구현한다:
   - transition key = `(case_id, from_state, to_state)`
   - duplicate transition은 기존 결과를 반환하고 새 transition record를 만들지 않는다
6. `audit_logs`를 event source로 구현한다:
   - INSERT만 사용하고 기존 audit log row는 UPDATE하지 않는다
   - schema: `id`, `case_id`, `action`, `evidence_chunk_ids`, `actor`, `timestamp`
   - `audit_logs`를 다시 재생하면 workflow state를 복원할 수 있어야 한다

## 검증
다음을 실행한다:

```bash
uv run pytest tests/test_case_factory.py tests/test_workflow_state.py
```

## 중단 조건
- transition이 human approval을 우회하면 중단한다.
- risk flag를 표현할 수 없으면 중단한다.
- 필요한 router 또는 retrieval 모듈이 없으면 중단한다.
- slot assembly가 LLM extraction이나 explicit하지 않은 inferred data를 요구하면 중단한다.
- duplicate transition이 두 번째 audit event를 만들면 중단한다.
- state를 표현하려면 audit log update가 필요하면 중단한다.
- missing metadata에 대한 silent fallback은 금지한다. 명시적 이유와 함께 blocked로 표시한다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```
