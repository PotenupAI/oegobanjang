# Mission 010: Risk Report Generation

## Goal

LLM 판단 JSON을 deterministic한 위험도 분류 결과와 기본 리포트로 변환한다.

위험도는 LLM 자유 판단에 맡기지 않는다. 이 mission은 허용된 risk enum과 level만 사용해 결과를 정규화하고, 담당자가 검토할 수 있는 기본 리포트를 생성하는 것이 목적이다.

---

## Required Reading

```txt
AGENTS.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/AI_OS_DESIGN.md
docs/SECURITY_GUARDRAILS.md
docs/EVIDENCE_LOG_SCHEMA.md
missions/active/008-rag-evidence-package.md
missions/active/009-llm-judgment-json-chain.md
```

---

## Target Files

```txt
backend/app/agent_runtime/reporting/risk.py
backend/app/agent_runtime/reporting/report.py

backend/app/agent_runtime/schemas/response.py
backend/app/agent_runtime/graph/nodes/final_response.py
backend/app/agent_runtime/graph/nodes/evidence_logger.py

backend/tests/test_report_generation.py
backend/tests/test_agent_workflow.py
backend/tests/test_evidence.py
```

---

## Scope

이번 mission에서 구현할 범위는 다음과 같다.

- risk flag enum 정규화
- risk level enum 정규화
- 허용되지 않은 risk type 거절
- judgment JSON에서 기본 리포트 생성
- 리포트에 요청 요약, 감지 의도, 근거, 위험도, 승인 필요 작업, 다음 조치, Evidence source_id 목록 포함
- approval_required가 true인 작업은 실행 버튼이 아니라 승인 필요 항목으로 표시
- 리포트 생성 이벤트를 Evidence Log 후보로 남김
- 민감정보 원문이 리포트에 포함되지 않도록 마스킹 유지

---

## Out of Scope

이번 mission에서 구현하지 않는다.

- 실제 PDF export
- 대외 제출용 문서 생성
- 메시지 발송
- frontend 리포트 화면
- 실제 LLM provider 연결
- 법률/노무 판단 확정

---

## Report Sections

```txt
1. 요청 요약
2. 감지된 업무 의도
3. 확인된 공식/템플릿 근거
4. 위험도 분류
5. 승인 필요한 작업
6. 다음 조치
7. Evidence source_id 목록
```

---

## Acceptance Criteria

- JSON judgment에서 deterministic report가 생성된다.
- 리포트는 7개 기본 섹션을 포함한다.
- risk type은 허용 enum 안에 있어야 한다.
- risk level은 `low`, `medium`, `high` 중 하나여야 한다.
- `approval_required=true`인 작업이 리포트에 명확히 표시된다.
- Evidence source_id가 리포트에서 숨겨지지 않는다.
- 민감정보 원문이 리포트에 남지 않는다.
- 리포트 생성 실패가 silent fallback으로 처리되지 않는다.

---

## Verification Commands

```bash
uv run pytest backend/tests/test_report_generation.py backend/tests/test_agent_workflow.py backend/tests/test_evidence.py
python scripts/run_evals.py --dataset workflow_e2e_cases --strict
python scripts/run_evals.py --dataset safety_guardrail_cases --strict
```

---

## Human Review Checklist

- [ ] 위험도 분류가 enum 기반인가?
- [ ] LLM 자유문이 risk type을 새로 만들 수 없게 되어 있는가?
- [ ] 리포트가 담당자 검토에 필요한 정보를 담는가?
- [ ] 승인 필요한 작업이 자동 실행처럼 보이지 않는가?
- [ ] Evidence source_id가 리포트에 남는가?
