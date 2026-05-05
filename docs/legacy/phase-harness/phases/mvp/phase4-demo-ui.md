# 4단계: 데모 UI

## 목표
request input, checklist output, evidence source ID, risk flag, approval state를 보여주는 작은 로컬 demo surface를 제공한다.

## 입력
- `docs/UI_GUIDE.md`
- `src/workforce_router.py`
- `src/workflow_state.py`
- `src/retrieve.py`
- `data/structured/companies.csv`
- `data/synthetic_cases/`

## 허용 쓰기
- `src/demo_app.py`
- `tests/test_demo_app.py`
- `README.md`

## 금지
- 마케팅 랜딩 페이지를 추가하지 않는다.
- candidate를 rank하지 않는다.
- evidence source ID를 숨기지 않는다.
- 외부 메시지를 보내지 않는다.

## 단계
1. demo response assembly 테스트를 추가한다.
2. 로컬 전용 demo function 또는 최소 app entrypoint를 구현한다.
3. demo 실행 방법을 문서화한다.

## 검증
다음을 실행한다:

```bash
uv run pytest tests/test_demo_app.py
```

## 중단 조건
- 필요한 workflow 모듈이 없다.
- UI가 legal interpretation이나 candidate ranking을 암시한다.
- evidence source ID를 사용할 수 없다.
- missing metadata에 대한 silent fallback은 금지한다. 명시적 이유와 함께 blocked로 표시한다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```
