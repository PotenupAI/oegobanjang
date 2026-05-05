# Mission 007: Frontend API Integration

## Goal

Mission 005에서 만든 관리자 dashboard skeleton을 backend API와 연결한다.

이 mission의 목표는 mock 화면을 실제 제품 흐름에 가까운 read-only 운영 화면으로 올리는 것이다. 승인, Evidence Log, Agent 실행 결과를 볼 수 있게 하되, 외부 발송/전송/제출은 여전히 자동 실행하지 않는다.

---

## Required Reading

```txt
AGENTS.md
README.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/API_CONTRACT.md
docs/SECURITY_GUARDRAILS.md
docs/EVIDENCE_LOG_SCHEMA.md
missions/active/005-frontend-dashboard.md
docs/legacy/phase-harness/PHASE_TO_MISSION_MAPPING.md
```

---

## Target Files

```txt
frontend/app/dashboard/page.tsx
frontend/app/approvals/page.tsx
frontend/app/evidence/page.tsx
frontend/app/workers/page.tsx
frontend/app/hiring/page.tsx
frontend/app/visa/page.tsx
frontend/app/documents/page.tsx
frontend/app/contacts/page.tsx

frontend/components/
frontend/features/dashboard/
frontend/features/approvals/
frontend/features/evidence/
frontend/lib/api.ts
frontend/types/

backend/app/api/v1/agent.py
backend/app/api/v1/approvals.py
backend/app/api/v1/evidence.py
backend/tests/test_agent_workflow.py
backend/tests/test_approvals.py
backend/tests/test_evidence.py
```

---

## Scope

이번 mission에서 구현할 범위는 다음과 같다.

- frontend API client의 response/error 계약 정리
- dashboard mock data를 backend 응답 기반 loader 또는 adapter로 교체
- approval list 화면을 backend approval API와 연결
- Evidence Log 화면을 request_id 조회 API와 연결
- Agent 실행 결과의 `approval_required`, `evidence_events`, `final_response` 표시
- 민감정보 마스킹 표시 유지
- 실패/로딩/빈 상태 UI 추가
- frontend 검증 스크립트 또는 실제 framework build 검증 정리

---

## Out of Scope

이번 mission에서 구현하지 않는다.

- 실제 외부 메시지 발송
- 행정사/노무사 패키지 전송
- 정부 포털 제출
- 완전한 인증/인가
- 복잡한 차트
- 모바일 최적화 완성
- candidate ranking 또는 nationality preference UI

---

## Acceptance Criteria

- dashboard가 backend API 응답 또는 adapter를 통해 데이터를 표시한다.
- approval 화면에서 `PENDING` 상태 작업을 볼 수 있다.
- Evidence 화면에서 request_id 기준 이벤트를 볼 수 있다.
- 승인 필요한 작업은 실행 버튼이 아니라 승인 흐름으로만 표시된다.
- 민감정보 원문은 화면에 표시되지 않는다.
- API 실패와 빈 데이터 상태가 사용자에게 명확히 보인다.
- backend tests와 frontend lint/test/build 검증이 통과한다.

---

## Verification Commands

```bash
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_approvals.py backend/tests/test_evidence.py
npm run lint --prefix frontend
npm run test --prefix frontend
npm run build --prefix frontend
```

---

## Human Review Checklist

- [ ] mock-only 화면에서 API 연결 화면으로 전환됐는가?
- [ ] 승인 필요한 작업이 자동 실행되지 않는가?
- [ ] Evidence Log 접근 경로가 명확한가?
- [ ] 민감정보가 마스킹되는가?
- [ ] API 실패/빈 상태가 처리되는가?
