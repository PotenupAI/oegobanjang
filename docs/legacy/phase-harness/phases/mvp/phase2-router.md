# 2단계: 라우터

## 목표
워크포스 요청 intent, `case_type`, optional phase routing을 deterministic하게 파싱한다.

참고: `company_id`, `headcount` 같은 slot extraction은 Phase 2 범위 밖이며 Phase 3 workflow input assembly에 속한다.

## 입력
- `01_workforce_agent_schema.md`
- `docs/DATA_GUIDE.md`
- `data/synthetic_cases/case_001.json`
- `data/synthetic_cases/case_002.json`
- `data/synthetic_cases/case_003.json`

## 허용 쓰기
- `src/workforce_router.py`
- `tests/test_workforce_router.py`

## 금지
- LLM을 호출하지 않는다.
- candidate를 rank하거나 recommend하지 않는다.
- user가 제공한 text를 넘어 nationality preference를 추론하지 않는다.
- data 파일을 수정하지 않는다.

## 단계
1. 허용되는 `case_type` 4개에 대한 테스트를 추가한다.
2. explicit case field와 흔한 한국어 query phrase를 바탕으로 simple deterministic routing을 구현한다.
3. ambiguous request에는 `blocked` 스타일 오류를 반환한다.

## 검증
다음을 실행한다:

```bash
uv run pytest tests/test_workforce_router.py
```

## 중단 조건
- route에 legal interpretation이 필요하다.
- 요청이 candidate ranking이나 nationality preference를 요구한다.
- synthetic case에 routing 정보가 충분하지 않다.
- missing metadata에 대한 silent fallback은 금지한다. 명시적 이유와 함께 blocked로 표시한다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```
