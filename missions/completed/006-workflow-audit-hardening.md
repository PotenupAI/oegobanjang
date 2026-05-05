# Mission 006: Workflow Audit Hardening

## Goal

Agent Runtime과 Approval/Evidence Log 흐름을 운영 가능한 감사 추적 구조로 강화한다.

Mission 001은 실행 흐름을 검증 가능한 skeleton으로 만들었다. 이 mission은 같은 흐름에서 중복 실행, 승인 우회, Evidence Log 누락, 민감정보 로그 저장을 더 엄격하게 막는 것이 목적이다.

---

## Required Reading

```txt
AGENTS.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/AI_OS_DESIGN.md
docs/GRAPH_STATE.md
docs/EVIDENCE_LOG_SCHEMA.md
docs/OBSERVABILITY.md
docs/SECURITY_GUARDRAILS.md
docs/legacy/phase-harness/ENGINEERING_PLAN.md
docs/legacy/phase-harness/PHASE_TO_MISSION_MAPPING.md
```

---

## Target Files

```txt
backend/app/agent_runtime/graph/state.py
backend/app/agent_runtime/graph/workflow.py
backend/app/agent_runtime/graph/nodes/approval_gate.py
backend/app/agent_runtime/graph/nodes/evidence_logger.py
backend/app/agent_runtime/schemas/evidence.py

backend/app/models/approval.py
backend/app/models/evidence.py
backend/app/schemas/approval.py
backend/app/schemas/evidence.py
backend/app/services/approval_service.py
backend/app/services/evidence_service.py

backend/tests/test_agent_workflow.py
backend/tests/test_approvals.py
backend/tests/test_evidence.py
backend/tests/test_workflow_state.py
backend/tests/test_pii_filter.py
```

---

## Scope

이번 mission에서 구현할 범위는 다음과 같다.

- request_id 기준 idempotency 규칙 정의
- 동일 request 재실행 시 중복 approval/evidence 생성 방지
- Evidence Log 이벤트 순서와 필수 이벤트 검증 강화
- 승인 필요한 action이 approval token 또는 explicit approval 없이 완료 상태로 넘어가지 않도록 차단
- Evidence Log에 원문 PII가 저장되지 않는지 테스트 강화
- audit replay 또는 event ordering을 위한 최소 구조 정의
- failure mode를 silent fallback 대신 blocked/error로 노출

---

## Out of Scope

이번 mission에서 구현하지 않는다.

- 실제 메시지 발송
- 실제 행정사/노무사 패키지 전달
- 외부 정부 포털 연동
- 완전한 DB migration 운영 체계
- LLM 기반 risk 판단
- 승인 token cryptographic signing 고도화

---

## Acceptance Criteria

- 동일 request_id 재실행이 중복 approval/evidence record를 만들지 않는다.
- 승인 필요한 action은 approval 없이 `completed` 상태로 전이되지 않는다.
- 필수 Evidence 이벤트가 순서대로 생성된다.
- Evidence Log 조회에서 request_id 단위 이벤트 추적이 가능하다.
- Evidence Log와 audit payload에 외국인등록번호, 여권번호, 전화번호 원문이 남지 않는다.
- 누락 metadata 또는 빈 evidence 결과가 silent fallback으로 처리되지 않는다.
- 관련 backend tests가 통과한다.

---

## Verification Commands

```bash
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_approvals.py backend/tests/test_evidence.py backend/tests/test_workflow_state.py backend/tests/test_pii_filter.py
python scripts/run_evals.py --dataset safety_guardrail_cases --strict
python scripts/run_evals.py --dataset workflow_e2e_cases --strict
```

---

## Human Review Checklist

- [ ] 승인 우회가 불가능한가?
- [ ] 중복 요청이 중복 side effect를 만들지 않는가?
- [ ] Evidence Log 필수 이벤트가 누락되지 않는가?
- [ ] 민감정보 원문이 저장되지 않는가?
- [ ] 실패가 명시적으로 blocked/error로 드러나는가?
