# Legacy Phase to Current Mission Mapping

이 문서는 예전 phase 기반 하네스 문서가 현재 `missions/active` 구조에서 어디로 흡수됐는지 정리한다.

현재 실행 기준은 `missions/active/*.md`이며, `docs/legacy/phase-harness/phases/**`는 실행 대상이 아니다.

## 대응표

| Legacy phase | 핵심 목적 | Current mission | 대응 상태 | 비고 |
|---|---|---|---|---|
| `phases/harness/phase0-harness-bootstrap.md` | Codex phase runner, phase template, harness test 구성 | 없음 | 아카이브됨 | 현재 구조는 phase runner 대신 `missions/` 문서를 작업 단위로 사용한다. 하네스 의도는 `missions/README.md`, `AGENTS.md`, `.claude/commands/*`에 분산 반영됐다. |
| `phases/mvp/phase1-data-schema.md` | 데이터 계약 고정, 공식 raw source 확인, RAG thin slice, retrieval eval | `002-rag-indexing.md` | 대부분 흡수 | 예전 `data/processed`, `src/ingest.py`, `eval/retrieval_eval.jsonl` 범위가 현재 `data-pipeline/`, `backend/app/agent_runtime/rag/`, `evals/datasets/rag_retrieval_cases.jsonl`로 이동했다. |
| `phases/mvp/phase1-data-schema.md` | company/candidate/synthetic/chunk/source schema 문서화와 contract test | `004-backend-core-api.md`, `002-rag-indexing.md` | 부분 흡수 | 현재 DB/API skeleton은 `004`, RAG metadata/chunk 계약은 `002`가 담당한다. 예전 `docs/DATA_GUIDE.md` 성격은 현재 `docs/DB_SCHEMA.md`, `docs/SCHEMA_CONTRACT.md`, `docs/RAG_STRATEGY.md`, `docs/EVAL_HARNESS.md`로 나뉜다. |
| `phases/mvp/phase1b-repair-synthetic-cases.md` | 손상된 synthetic case fixture 복구 | 없음 | 현재 mission 없음 | 현재 active mission에는 synthetic case 복구 전용 mission이 없다. 필요하면 `006-synthetic-case-fixtures.md` 같은 별도 mission으로 분리하는 것이 맞다. |
| `phases/mvp/phase1c-chunk-and-embedding.md` | structured chunking, embedding cache, dense/hybrid retrieval, Hit@3 향상 | `002-rag-indexing.md` | 축소 흡수 | 현재 mission 002는 Chroma 적재용 JSONL, metadata schema, retrieval eval 실행 가능성을 요구한다. OpenAI embedding cache, hybrid retriever, `Hit@3 >= 90%` 같은 고도화 조건은 현재 mission 범위보다 넓다. |
| `phases/mvp/phase2-router.md` | deterministic intent/case_type/phase routing | `001-agent-runtime-skeleton.md` | 흡수 | 현재 `001`의 Intent Router가 초기 intent 목록과 사용자 요청 기반 intent 분류를 담당한다. 예전 workforce-specific `case_type` routing은 현재 Agent Runtime skeleton 안으로 통합됐다. |
| `phases/mvp/phase2a-pii-middleware.md` | router/retriever/LLM 전 PII 마스킹 | `001-agent-runtime-skeleton.md`, `003-approval-evidence-log.md`, `004-backend-core-api.md` | 흡수 | 현재 PII 마스킹은 Agent Runtime 입력/출력 안전성, Evidence Log 민감정보 금지, backend logging 안전성에 걸쳐 있다. 단독 phase보다 cross-cutting guardrail로 보는 것이 맞다. |
| `phases/mvp/phase3-state-machine.md` | workflow state machine, risk flag, human approval, audit log | `001-agent-runtime-skeleton.md`, `003-approval-evidence-log.md` | 대부분 흡수 | 현재 `001`은 `Intent Router -> Planner -> Executor -> Approval Gate -> Evidence Logger -> Final Response` 흐름을 만들고, `003`은 승인 상태와 Evidence Log 저장/조회 계약을 담당한다. |
| `phases/mvp/phase4-demo-ui.md` | request input, checklist output, evidence source ID, risk flag, approval state를 보여주는 demo UI | `005-frontend-dashboard.md` | 확장 흡수 | 예전 demo app은 로컬 surface였고, 현재 `005`는 Next.js/React 관리자 dashboard route와 approvals/evidence 화면 skeleton을 요구한다. |
| `phases/templates/phase_template.md` | phase 실행 문서 템플릿 | 없음 | 아카이브됨 | 현재 템플릿 역할은 `missions/README.md`의 mission 작성 형식이 대체한다. |

## 현재 Mission 기준 요약

| Current mission | 흡수한 legacy 범위 | 아직 별도 판단이 필요한 legacy 잔여 |
|---|---|---|
| `001-agent-runtime-skeleton.md` | Phase 2 router, Phase 2A PII guardrail 일부, Phase 3 state flow 일부 | workforce-specific `case_type` routing을 제품 API에서 얼마나 노출할지 결정 필요 |
| `002-rag-indexing.md` | Phase 1 RAG thin slice, Phase 1C chunk/index/eval 일부 | embedding cache, hybrid retriever, `Hit@3 >= 90%` 고도화는 별도 mission 후보 |
| `003-approval-evidence-log.md` | Phase 2A PII logging guardrail 일부, Phase 3 human approval/audit log | approval token signing, event-source replay 수준의 audit log는 별도 고도화 후보 |
| `004-backend-core-api.md` | Phase 1 데이터 계약 중 DB/API skeleton 영역 | synthetic case fixture 복구와 structured demo data 계약은 별도 mission 후보 |
| `005-frontend-dashboard.md` | Phase 4 demo UI | 실제 API 연동, Next.js 런타임 완성, browser verification은 후속 mission 후보 |

## 후속 Mission 후보

| 후보 mission | 근거가 되는 legacy phase | 목적 |
|---|---|---|
| `006-synthetic-case-fixtures.md` | Phase 1B | demo-only synthetic case fixture를 현재 `evals/`와 backend workflow 테스트에 맞게 정리한다. |
| `007-rag-retrieval-upgrade.md` | Phase 1C | embedding cache, hybrid retrieval, stricter chunk-level citation eval을 구현한다. |
| `008-workflow-audit-hardening.md` | Phase 3, `ENGINEERING_PLAN.md` | idempotency, insert-only audit log replay, approval token signing을 강화한다. |
| `009-frontend-api-integration.md` | Phase 4, Mission 005 | mock dashboard를 backend API와 연결하고 실제 Next.js build/browser verification을 수행한다. |
