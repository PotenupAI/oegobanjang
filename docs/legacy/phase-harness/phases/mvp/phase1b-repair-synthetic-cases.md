# 1B단계: Synthetic Case 복구

## 목표
손상된 synthetic case fixture를 복구해서 demo-only data로 유지하고, Phase 2의 deterministic routing 검증에 사용할 수 있게 한다.

## 입력
- `docs/DATA_GUIDE.md`
- `data/synthetic_cases/case_001.json`
- `data/synthetic_cases/case_002.json`
- `data/synthetic_cases/case_003.json`

## 허용 쓰기
- `data/synthetic_cases/case_001.json`
- `data/synthetic_cases/case_002.json`
- `data/synthetic_cases/case_003.json`
- `phases/mvp/phase1b-repair-synthetic-cases.status.json`

## 금지
- 코드 파일을 수정하지 않는다.
- 공식 legal claim이나 production API response를 추가하지 않는다.
- JSON 복구와 demo-safe wording 정리 외에 synthetic case 의도를 바꾸지 않는다.

## 단계
1. 3개의 synthetic case JSON 파일이 정상적으로 파싱되도록 복구한다.
2. Phase 2 routing에 필요한 기존 case type, phase, fixture 의도를 유지한다.
3. `human_approval_required`를 true로 유지하고 demo-only 평가 기준을 보존한다.
4. 검증 결과를 Phase 1B status 파일에 기록한다.

## 검증
다음을 실행한다:

```bash
uv run pytest tests/test_data_contracts.py
Get-ChildItem data/synthetic_cases -Filter '*.json' | ForEach-Object { Get-Content $_.FullName | ConvertFrom-Json | Out-Null }
```

## 중단 조건
- synthetic case를 유효하게 만들기 위해 지어낸 legal evidence가 필요하다.
- case type이나 phase 의도를 바꾸지 않으면 fixture를 복구할 수 없다.
- missing metadata에 대한 silent fallback은 금지한다. 명시적 이유와 함께 blocked로 표시한다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```
