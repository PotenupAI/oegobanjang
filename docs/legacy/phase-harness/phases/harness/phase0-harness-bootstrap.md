# 0단계: 하네스 부트스트랩

## 목표
WorkBridge용 Codex harness 기반을 만든다. 이후 작업이 경계가 있는 Phase 파일을 통해 실행되도록 하기 위함이다.

## 입력
- `01_workforce_agent_schema.md`
- `02_week1_checklist_eval.md`
- `03_codex_harness_engineering.md`

## 허용 쓰기
- `AGENTS.md`
- `phases/templates/phase_template.md`
- `phases/harness/phase0-harness-bootstrap.md`
- `scripts/__init__.py`
- `scripts/execute_codex.py`
- `tests/test_execute_codex.py`

## 금지
- workforce schema, Week 1 checklist, mock data를 수정하지 않는다.
- 외부 의존성을 추가하지 않는다.
- 테스트에서 `codex exec`를 호출하지 않는다.
- 공식 EPS/legal source 데이터를 생성하거나 지어내지 않는다.

## 단계
1. `AGENTS.md`에 프로젝트 수준의 harness 지침을 추가한다.
2. 필요한 harness 블록을 포함한 재사용 가능한 Phase template을 추가한다.
3. 이 bootstrap Phase 파일을 완료된 harness Phase로 추가한다.
4. `scripts/execute_codex.py`를 자동 Phase runner로 구현한다.
5. Phase 선택, status 파싱, command 구성, status 파일 쓰기 테스트를 추가한다.

## 검증
다음을 실행한다:

```bash
uv run pytest tests/test_execute_codex.py
```

## 중단 조건
- `uv run pytest tests/test_execute_codex.py`를 실행할 수 없다.
- runner가 completed, blocked, error 상태를 deterministic하게 판단하지 못한다.
- Phase template에 `Allowed Writes`, `Forbidden`, `Verification`, `Stop Conditions` 중 하나가 빠져 있다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```
