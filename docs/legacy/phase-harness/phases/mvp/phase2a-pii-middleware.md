# 2A단계: PII 필터 미들웨어

## 목표
어떤 router, retriever, LLM 호출보다도 먼저 외국인등록번호, 여권번호, 휴대전화번호를 마스킹한다.

## 입력
- `docs/DATA_GUIDE.md`
- `src/workforce_router.py`
- `src/retrieve.py`

## 허용 쓰기
- `src/middleware/pii_filter.py`
- `tests/test_pii_filter.py`

## 금지
- raw PII를 어디에도 저장하지 않는다.
- raw PII를 `retrieve.py`나 어떤 LLM에도 전달하지 않는다.
- 외부 저장소나 network call을 추가하지 않는다.

## 단계
1. deterministic PII masking middleware를 구현한다.
2. 13자리 외국인등록번호를 `▲▲▲▲▲▲-▲▲▲▲▲▲▲`로 마스킹한다.
3. downstream router 또는 retriever 호출 전에 passport number와 mobile phone number도 마스킹한다.
4. 주민등록번호, 여권번호, 휴대전화번호, 이미 마스킹된 텍스트를 다루는 테스트를 추가한다.

## 검증
다음을 실행한다:

```bash
uv run pytest tests/test_pii_filter.py
```

Required test cases:
- 13자리 외국인등록번호가 `▲▲▲▲▲▲-▲▲▲▲▲▲▲`로 마스킹되어야 한다.
- raw PII가 middleware output에 나타나지 않아야 한다.
- 마스킹된 output은 Phase 2 router에 안전하게 전달할 수 있어야 한다.

## 중단 조건
- 마스킹 규칙이 output에 raw PII를 남기면 중단한다.
- middleware가 raw PII 저장을 요구하면 중단한다.
- router나 retriever가 raw PII 없이 호출될 수 없으면 중단한다.
- missing metadata에 대한 silent fallback은 금지한다. 명시적 이유와 함께 blocked로 표시한다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```
