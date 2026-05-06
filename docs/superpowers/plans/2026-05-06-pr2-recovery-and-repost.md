# PR 2 Recovery And Repost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the closed PR #2 work on top of latest `origin/main` without replacing the Phase 3a/3b/3c LangGraph, async DB, API, and eval structure.

**Architecture:** Treat latest `origin/main` as the source of truth. Port only small, testable feature slices from `port-rag-indexing-new-structure`; do not merge or rebase the old branch wholesale. Preserve LangGraph/checkpointer runtime, async SQLAlchemy session, current FastAPI contracts, and Phase 3 eval harness.

**Tech Stack:** FastAPI, LangGraph, async SQLAlchemy, Pydantic, pytest under `backend/tests`, JSONL evals under `evals/datasets`, Next.js frontend skeleton.

---

## Current Facts

- Closed PR: `https://github.com/PotenupAI/oegobanjang/pull/2`
- GitHub PR state at review time: `closed`, `merged=false`, `draft=true`, `mergeable=false`
- Old branch: `port-rag-indexing-new-structure`
- Old head: `73c2c636689eb1ab8815f2ad58efc17833b4d036`
- GitHub commit status for old head: empty status list, so no confirmed CI signal
- Latest base checked locally: `origin/main` at `92e053c`
- PR size against latest main: `213 files changed, 48234 insertions, 94 deletions`
- Dry merge conflict set: 21 files, concentrated in agent runtime, API, DB session, router, and eval JSONL datasets
- Do not use the old branch's `backend/app/db/session.py`; latest main uses async SQLAlchemy and must stay that way
- Do not replace latest main's `backend/app/agent_runtime/graph/workflow.py`; latest main uses LangGraph `StateGraph` plus `MemorySaver`

## Confirmed Conflict Files

The dry merge conflict set was:

```txt
backend/app/agent_runtime/agents/hiring_agent.py
backend/app/agent_runtime/graph/__init__.py
backend/app/agent_runtime/graph/nodes/__init__.py
backend/app/agent_runtime/graph/nodes/approval_gate.py
backend/app/agent_runtime/graph/nodes/evidence_logger.py
backend/app/agent_runtime/graph/nodes/executor.py
backend/app/agent_runtime/graph/nodes/final_response.py
backend/app/agent_runtime/graph/nodes/intent_router.py
backend/app/agent_runtime/graph/nodes/planner.py
backend/app/agent_runtime/graph/state.py
backend/app/agent_runtime/graph/workflow.py
backend/app/agent_runtime/middleware/__init__.py
backend/app/agent_runtime/middleware/pii_filter.py
backend/app/agent_runtime/schemas/evidence.py
backend/app/agent_runtime/schemas/state.py
backend/app/api/v1/agent.py
backend/app/api/v1/router.py
backend/app/db/session.py
evals/datasets/intent_router_cases.jsonl
evals/datasets/safety_guardrail_cases.jsonl
evals/datasets/workflow_e2e_cases.jsonl
```

## Pre-Work: Protect Current Dirty Worktree

**Files:**
- Preserve current local changes shown by `git status --short`
- Do not stage unrelated journal or mission edits into recovery PRs

- [x] **Step 1: Record dirty state**

Run:

```bash
git status --short --branch
```

Expected: dirty files may include `docs/journal/*`, `missions/README.md`, `missions/active/014-agent-output-aggregation.md`, and local plan docs.

- [x] **Step 2: Create a safety branch before any branch surgery**

Run:

```bash
git switch -c backup/pr2-recovery-dirty-2026-05-06
git add docs/superpowers/plans/2026-05-06-pr2-recovery-and-repost.md
git status --short
```

Expected: only this plan file is staged for the backup commit if committing is desired.

- [x] **Step 3: Isolate implementation in a clean worktree**

Run:

```bash
git fetch origin
git worktree add ..\WorkBridge-pr2-recovery origin/main
cd ..\WorkBridge-pr2-recovery
git switch -c pr2-runtime-guardrail-port
```

Expected: clean checkout based on latest `origin/main`.

## PR 1: Runtime Guardrail Port, LangGraph Preserved

**Files:**
- Modify: `backend/app/agent_runtime/graph/nodes/intent_router.py`
- Modify: `backend/app/agent_runtime/graph/nodes/planner.py`
- Modify: `backend/app/agent_runtime/graph/nodes/executor.py`
- Modify: `backend/app/agent_runtime/graph/nodes/approval_gate.py`
- Modify: `backend/app/agent_runtime/graph/nodes/final_response.py`
- Modify: `backend/app/agent_runtime/schemas/state.py`
- Modify or extend: `backend/app/agent_runtime/middleware/pii_filter.py`
- Test: `backend/tests/test_agent_workflow.py`
- Test: `backend/tests/test_guardrails.py`
- Test: `backend/tests/test_workflow_state.py`
- Eval: `evals/datasets/safety_guardrail_cases.jsonl`
- Eval: `evals/datasets/workflow_e2e_cases.jsonl`

- [x] **Step 1: Inspect old runtime commit without applying it**

Run:

```bash
git show --stat d2e70e7
git show d2e70e7 -- backend/app/agent_runtime/graph/workflow.py backend/app/db/session.py
```

Expected: old commit contains useful guardrail behavior but also replaces runtime structure. Do not cherry-pick it whole.

- [x] **Step 2: Add focused tests first**

Add tests that prove:

- unsupported legal judgment is refused
- external send or handoff requests set approval pending
- raw PII does not appear in final response or evidence summaries
- existing LangGraph workflow still returns `ForeignHiringState`

Run:

```bash
uv run python -m pytest backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py backend/tests/test_workflow_state.py
```

Expected before implementation: at least one new assertion fails.

- [x] **Step 3: Port only behavior into latest main nodes**

Implementation rule:

- Keep `backend/app/agent_runtime/graph/workflow.py` as LangGraph `StateGraph`
- Keep `backend/app/agent_runtime/runner.py` async
- Keep `backend/app/db/session.py` async SQLAlchemy
- Add guardrail and approval behavior inside existing nodes and schemas only

- [x] **Step 4: Verify PR 1**

Run:

```bash
uv run python -m pytest backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py backend/tests/test_workflow_state.py
uv run python scripts/run_evals.py --dataset safety_guardrail_cases --strict
uv run python scripts/run_evals.py --dataset workflow_e2e_cases --strict
```

Expected: all pass.

- [x] **Step 5: Commit PR 1**

Run:

```bash
git add backend/app/agent_runtime backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py backend/tests/test_workflow_state.py evals/datasets/safety_guardrail_cases.jsonl evals/datasets/workflow_e2e_cases.jsonl
git commit -m "feat(agent-runtime): preserve langgraph guardrails"
git push -u origin pr2-runtime-guardrail-port
```

Checkpoint result:

- Worktree: `C:\WorkBridge-pr2-recovery`
- Branch: `pr2-runtime-guardrail-port`
- Commit: `1768b82 feat(agent-runtime): preserve langgraph guardrails`
- Draft PR: `https://github.com/PotenupAI/oegobanjang/pull/3`
- Focused tests: `5 passed`
- Strict evals: `safety_guardrail_cases` and `workflow_e2e_cases` passed with `0 issues`
- Full backend suite is blocked by existing RAG collection error: `ModuleNotFoundError: No module named 'app.agent_runtime.rag.evaluate'`

## PR 2: LLM Judgment Runtime Guard

**Files:**
- Create or modify: `backend/app/agent_runtime/llm/client.py`
- Create or modify: `backend/app/agent_runtime/llm/parser.py`
- Create or modify: `backend/app/agent_runtime/llm/judgment_chain.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/agent_runtime/graph/nodes/final_response.py`
- Test: `backend/tests/test_llm_judgment_chain.py`

- [ ] **Step 1: Branch from PR 1 or latest main after PR 1 merges**

Run:

```bash
git switch main
git pull --rebase origin main
git switch -c pr2-llm-judgment-guard
```

- [ ] **Step 2: Port provider guard without making real calls by default**

Rules:

- `REAL_LLM_ENABLED=false` must be the safe default
- provider errors must block or fall back explicitly
- tests must use fake/static client behavior
- no live API key is required for tests

- [ ] **Step 3: Verify PR 2**

Run:

```bash
uv run python -m pytest backend/tests/test_llm_judgment_chain.py
uv run python -m pytest backend/tests
```

Expected: backend tests pass without a real LLM provider call.

## PR 3: RAG Source Metadata And Retrieval Scoring

**Files:**
- Modify: `backend/app/agent_runtime/rag_hyunwook/*` or current latest-main RAG path, after inspection
- Modify: `data-pipeline/ingest.py`
- Modify: `scripts/run_evals.py` only if latest main does not already support required strict checks
- Add or modify: `evals/datasets/rag_retrieval_cases.jsonl`
- Add official raw/source manifest files only if they are not already present in latest main's accepted location
- Test: `backend/tests/test_rag_indexing.py`
- Test: `backend/tests/test_rag_eval_dataset.py`

- [ ] **Step 1: Compare old RAG files with latest main**

Run:

```bash
git diff --name-status origin/main...port-rag-indexing-new-structure -- data-pipeline backend/app/agent_runtime/rag* evals/datasets/rag_retrieval_cases.jsonl
```

- [ ] **Step 2: Port metadata/scoring only into latest RAG module**

Rules:

- Follow latest main's `rag_hyunwook` path if that is the active implementation
- Keep source IDs stable
- Keep official source metadata separate from generated chunks
- Do not import the old deterministic runtime into RAG code

- [ ] **Step 3: Verify PR 3**

Run:

```bash
uv run python -m pytest backend/tests/test_rag_indexing.py backend/tests/test_rag_eval_dataset.py
uv run python scripts/run_evals.py --dataset rag_retrieval_cases --strict
```

Expected: structural eval and RAG tests pass.

## PR 4: Backend API Resource Scaffold, Async Contract Preserved

**Files:**
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/api/v1/*.py` only for resources being introduced
- Modify: `backend/app/services/*.py` only if called by routes
- Modify: `backend/app/schemas/*.py` only for public API schemas
- Test: `backend/tests/test_health.py`
- Add focused API tests if routes are not already covered

- [ ] **Step 1: Keep `agent.py` contract from latest main**

Rules:

- `/api/v1/agent/run` remains async
- `AgentRunResponse` continues to match latest main unless a test-driven change requires extension
- `get_agent_state` remains compatible with LangGraph checkpointer state
- Do not reintroduce sync placeholder DB sessions

- [ ] **Step 2: Add only one resource group per commit**

Suggested order:

1. approvals
2. evidence
3. workers/companies/contacts/documents/hiring/visas, only if needed by frontend

- [ ] **Step 3: Verify PR 4**

Run:

```bash
uv run python -m pytest backend/tests
```

Expected: backend test suite passes.

## PR 5: Frontend Dashboard And API Fallback

**Files:**
- Modify: `frontend/app/*`
- Modify: `frontend/components/*`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/types/index.ts`
- Test or script: `frontend/scripts/validate-frontend.mjs`

- [ ] **Step 1: Port frontend without backend contract drift**

Rules:

- The frontend must call current API response shapes
- Mock fallback is allowed when backend is unavailable
- Do not add marketing pages; keep app/dashboard first

- [ ] **Step 2: Verify PR 5**

Run:

```bash
npm run build
npm run test
```

Expected: frontend build and tests pass.

## PR 6: Docs, Missions, Taxonomy

**Files:**
- Modify: `missions/README.md`
- Modify or add: `missions/completed/*.md`
- Modify: `docs/EVIDENCE_LOG_SCHEMA.md`
- Modify: `docs/OBSERVABILITY.md`
- Add or modify: `taxonomy.md`
- Modify: `FOLDER_STRUCTURE.md` if file/folder structure changed

- [ ] **Step 1: Update docs after code PRs, not before**

Rules:

- Do not mark missions completed until their corresponding code PR has merged
- Keep `missions/active/*` as the current implementation contract
- Update `FOLDER_STRUCTURE.md` whenever committed structure changes

- [ ] **Step 2: Verify docs PR**

Run:

```bash
git diff --check
uv run python scripts/run_evals.py --all --strict
```

Expected: no whitespace errors; eval structural checks pass.

## Mission 014 Sequencing

Mission 014 should start only after PR 1 lands, because it depends on the current LangGraph runtime and approval/evidence behavior being stable.

Mission 014 adaptation decision:

- Latest main already has `backend/app/agent_runtime/schemas/agent.py` with `AgentOutput`
- Prefer extending that schema or adding a focused `AggregatedCaseOutput` next to it
- Only create `backend/app/agent_runtime/schemas/agent_output.py` if there is a clear import-cycle or compatibility reason

Mission 014 first PR should touch only:

- `backend/app/agent_runtime/schemas/agent.py`
- `backend/app/agent_runtime/schemas/state.py`
- `backend/app/agent_runtime/graph/nodes/aggregator.py`
- `backend/app/agent_runtime/graph/nodes/executor.py`
- `backend/app/agent_runtime/graph/nodes/approval_gate.py`
- `backend/app/agent_runtime/graph/nodes/final_response.py`
- `backend/app/agent_runtime/graph/workflow.py`
- `backend/tests/test_agent_aggregation.py`
- `backend/tests/test_agent_workflow.py`
- `evals/datasets/workflow_e2e_cases.jsonl`

## Stop Conditions

Stop and reassess if any of these happen:

- A patch wants to replace `backend/app/agent_runtime/graph/workflow.py` wholesale
- A patch wants to replace async SQLAlchemy with sync placeholders
- A patch changes more than one PR slice's ownership boundary
- Eval JSONL becomes invalid or mixes old Phase 1C cases with Phase 3 cases without explicit schema checks
- Tests need a real LLM provider or real external submission

## Final Verification Before Any New PR Is Marked Ready

Run:

```bash
uv run python -m pytest backend/tests
uv run python scripts/run_evals.py --dataset intent_router_cases --strict
uv run python scripts/run_evals.py --dataset safety_guardrail_cases --strict
uv run python scripts/run_evals.py --dataset workflow_e2e_cases --strict
uv run python scripts/run_evals.py --dataset rag_retrieval_cases --strict
npm run build
npm run test
```

Expected: all pass, or the PR body must state the exact failing command and why it is not part of that PR's scope.
