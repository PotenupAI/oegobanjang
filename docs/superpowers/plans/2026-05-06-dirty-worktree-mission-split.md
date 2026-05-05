# Dirty Worktree Mission Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use execution checklists. Do not proceed to the next checkpoint until the current checkpoint is verified.

**Goal:** Turn the current mixed WorkBridge dirty tree into reviewable, mission-scoped checkpoint commits or PR candidates without losing work.

**Architecture:** Snapshot first, then classify paths, then stage and commit in mission order. The current branch should stay as-is until the split is complete. No merge, push, or full-tree PR before scoped commits exist.

**Tech Stack:** Git, PowerShell, uv/pytest, npm, WorkBridge mission docs, eval datasets.

---

## Why This Plan Exists

The current worktree contains multiple kinds of work at once:

- Mission 001 agent runtime and safety gap closing
- RAG source, chunk, metadata, and retrieval hardening
- document check / hiring agent connection work
- LLM judgment and report-generation runtime work
- frontend API integration skeleton
- docs, taxonomy, legacy mapping, journal updates
- local helper scripts and generated artifacts

So the right answer is not "discard" and not "PR everything." The right answer is to preserve everything, then separate it into reviewable units.

Recommended current product choice from the completion prompt:

```txt
Keep the branch as-is
```

Then run this split plan.

---

## Safety Rules

- Do not run `git reset --hard`.
- Do not discard untracked files.
- Do not merge into `main` yet.
- Do not push a giant mixed PR.
- Do not stage `.env`, local secrets, cache folders, virtualenvs, or generated Chroma/vector DB folders.
- If `uv` fails from Windows cache permissions, rerun the same verification command through the already approved elevated `uv run` path.
- Treat `FOLDER_STRUCTURE.md` as a companion doc when tracked structure changes.

---

## Checkpoint 0: Preserve The Dirty Tree

Create a recoverable local checkpoint before splitting.

Commands:

```powershell
git status --short
git branch checkpoint/workbridge-before-mission-split-2026-05-06
git diff --name-only
```

Inspect for secrets or accidental local-only files:

```powershell
git status --short | Select-String -Pattern "\.env|secret|token|key|\.venv|node_modules|chroma|cache"
```

If clean enough to snapshot locally:

```powershell
git add -A
git commit -m "chore: checkpoint mixed WorkBridge mission work"
git branch checkpoint/workbridge-mixed-work-2026-05-06
git reset --mixed HEAD~1
```

Expected result:

- One local checkpoint branch points to the full mixed snapshot.
- The working tree is dirty again and ready for selective staging.
- Nothing has been pushed or merged.

---

## Checkpoint 1: Mission 001 Runtime And Guardrail Commit

Purpose: isolate the agent runtime acceptance gap work.

Likely files:

```txt
backend/app/agent_runtime/agents/hiring_agent.py
backend/app/agent_runtime/guardrails.py
backend/app/agent_runtime/middleware/
backend/app/agent_runtime/graph/__init__.py
backend/app/agent_runtime/graph/nodes/__init__.py
backend/app/agent_runtime/graph/nodes/approval_gate.py
backend/app/agent_runtime/graph/nodes/evidence_logger.py
backend/app/agent_runtime/graph/nodes/final_response.py
backend/app/agent_runtime/graph/nodes/intent_router.py
backend/app/agent_runtime/graph/nodes/planner.py
backend/app/agent_runtime/graph/state.py
backend/app/agent_runtime/schemas/evidence.py
backend/app/agent_runtime/schemas/state.py
backend/app/agent_runtime/tools/quota_tool.py
backend/tests/test_agent_workflow.py
backend/tests/test_approvals.py
backend/tests/test_evidence.py
backend/tests/test_eval_runner.py
backend/tests/test_guardrails.py
backend/tests/test_pii_filter.py
backend/tests/test_workflow_state.py
evals/datasets/intent_router_cases.jsonl
evals/datasets/safety_guardrail_cases.jsonl
evals/datasets/workflow_e2e_cases.jsonl
scripts/run_evals.py
```

Use `git add -p` for overlapping files such as `workflow.py`, `executor.py`, and `final_response.py` if they also contain later RAG or LLM changes.

Verification:

```powershell
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_approvals.py backend/tests/test_evidence.py backend/tests/test_eval_runner.py backend/tests/test_guardrails.py backend/tests/test_pii_filter.py backend/tests/test_workflow_state.py
uv run python scripts/run_evals.py --dataset intent_router_cases
uv run python scripts/run_evals.py --dataset safety_guardrail_cases
uv run python scripts/run_evals.py --dataset workflow_e2e_cases
```

Commit:

```powershell
git commit -m "feat(agent-runtime): close Mission 001 safety acceptance gaps"
```

Done when:

- message-based forbidden requests are blocked
- approval-required requests stay pending
- canonical evidence `event_type` is emitted
- eval runner fails on runtime mismatches

---

## Checkpoint 2: RAG Source And Metadata Hardening Commit

Purpose: isolate official source expansion, chunk metadata normalization, and retrieval eval hardening.

Likely files:

```txt
backend/app/agent_runtime/rag/evidence_package.py
backend/tests/test_evidence_package.py
backend/tests/test_rag_eval_dataset.py
backend/tests/test_rag_indexing.py
backend/tests/test_rag_source_manifest.py
data-pipeline/raw/eps_allowed_industries_001.html
data-pipeline/raw/eps_application_guide_001.html
data-pipeline/raw/eps_employer_process_001.html
data-pipeline/raw/eps_employer_scoring_001.html
data-pipeline/raw/law_foreign_worker_act_001.html
data-pipeline/raw/law_form_employment_change_001.pdf
data-pipeline/raw/source_manifest.json
data-pipeline/seed/sample_policy_docs.jsonl
data-pipeline/processed/chunks/all_chunks.jsonl
data-pipeline/processed/chunks/form_chunks.jsonl
data-pipeline/processed/chunks/general_chunks.jsonl
data-pipeline/processed/chunks/procedure_chunks.jsonl
data-pipeline/processed/chunks/regulation_chunks.jsonl
data-pipeline/processed/chunks/safety_chunks.jsonl
data-pipeline/processed/chunks/template_chunks.jsonl
evals/datasets/rag_retrieval_cases.jsonl
scripts/ingest_rag_docs.py
```

Verification:

```powershell
uv run python scripts/ingest_rag_docs.py
uv run pytest backend/tests/test_rag_indexing.py backend/tests/test_rag_eval_dataset.py backend/tests/test_rag_source_manifest.py backend/tests/test_evidence_package.py
uv run python scripts/run_evals.py --dataset rag_retrieval_cases
```

If the repo has an actual retrieval scorer command, also run it and record `Hit@3`.

Commit:

```powershell
git commit -m "feat(rag): harden official source metadata and retrieval fixtures"
```

Done when:

- source manifest has 20+ planned or collected official sources
- chunks carry normalized metadata
- retrieval eval has 20+ cases
- evidence package uses real retrieved chunks rather than fake data

---

## Checkpoint 3: Document Check And Hiring Agent Connection Commit

Purpose: isolate the workforce agent connection to document requirements and evidence packages.

Likely files:

```txt
backend/app/agent_runtime/tools/document_check_tool.py
backend/app/agent_runtime/graph/nodes/executor.py
backend/app/agent_runtime/graph/workflow.py
backend/tests/test_document_check_tool.py
backend/tests/test_agent_workflow.py
```

Use `git add -p` for `executor.py`, `workflow.py`, and `test_agent_workflow.py` because they may contain Mission 001 and LLM-runtime changes.

Verification:

```powershell
uv run pytest backend/tests/test_document_check_tool.py backend/tests/test_agent_workflow.py
```

Commit:

```powershell
git commit -m "feat(workforce): connect hiring flow to document gap checks"
```

Done when:

- hiring flow returns document gaps
- document output is checklist/readiness oriented, not legal certainty
- approval and evidence behavior stays unchanged

---

## Checkpoint 4: LLM Judgment And Report Runtime Commit

Purpose: isolate fake LLM judgment chain, structured report generation, and optional runtime mode work.

Likely files:

```txt
backend/app/agent_runtime/llm/
backend/app/agent_runtime/reporting/
backend/app/agent_runtime/schemas/response.py
backend/app/agent_runtime/graph/workflow.py
backend/app/agent_runtime/graph/nodes/final_response.py
backend/app/schemas/agent.py
backend/app/services/agent_service.py
backend/app/api/v1/agent.py
backend/tests/test_llm_judgment_chain.py
backend/tests/test_report_generation.py
backend/tests/test_agent_workflow.py
missions/completed/008-rag-evidence-package.md
missions/completed/009-llm-judgment-json-chain.md
missions/completed/010-risk-report-generation.md
missions/completed/011-judgment-runtime-mode.md
missions/active/012-langchain-judgment-adapter.md
missions/active/013-real-llm-provider-integration.md
```

Verification:

```powershell
uv run pytest backend/tests/test_llm_judgment_chain.py backend/tests/test_report_generation.py backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py backend/tests/test_evidence.py
```

Commit:

```powershell
git commit -m "feat(judgment): add structured LLM judgment runtime mode"
```

Done when:

- deterministic runtime remains the default
- fake LLM tests do not call the network
- unsupported intents are blocked before LLM execution
- generated report avoids legal certainty and auto-submission language

---

## Checkpoint 5: Backend API And Core Plumbing Commit

Purpose: isolate FastAPI/API/core changes that are not strictly part of the agent internals.

Likely files:

```txt
backend/app/api/v1/agent.py
backend/app/api/v1/health.py
backend/app/api/v1/router.py
backend/app/core/exceptions.py
backend/app/core/logging.py
backend/app/core/responses.py
backend/app/core/security.py
backend/app/db/base.py
backend/app/db/session.py
backend/app/main.py
backend/app/schemas/agent.py
backend/app/services/agent_service.py
```

Before staging, inspect each file. If a file only exists because of scaffolding and has no tested behavior, leave it unstaged for a later cleanup commit.

Verification:

```powershell
uv run pytest backend/tests
```

Commit:

```powershell
git commit -m "feat(api): expose agent runtime response plumbing"
```

Done when:

- `/api/v1/agent/run` still works
- response schema remains backward compatible
- backend tests pass

---

## Checkpoint 6: Frontend API Integration Skeleton Commit

Purpose: isolate frontend work so backend reviewers do not have to review UI scaffolding at the same time.

Likely files:

```txt
frontend/app/layout.tsx
frontend/app/page.tsx
frontend/app/styles.css
frontend/app/approvals/
frontend/app/contacts/
frontend/app/dashboard/
frontend/app/documents/
frontend/app/evidence/
frontend/app/hiring/
frontend/app/visa/
frontend/app/workers/
frontend/components/AppShell.tsx
frontend/components/StatusBadge.tsx
frontend/features/dashboard/mockData.ts
frontend/lib/api.ts
frontend/lib/constants.ts
frontend/package.json
frontend/package-lock.json
frontend/scripts/
frontend/types/index.ts
```

Verification:

```powershell
npm run build
npm run test:run
```

Commit:

```powershell
git commit -m "feat(frontend): scaffold WorkBridge agent dashboard routes"
```

Done when:

- frontend builds
- empty `.gitkeep` deletions are intentional
- UI routes are clearly separated from backend runtime work

---

## Checkpoint 7: Docs, Taxonomy, Legacy Mapping, And Journal Commit

Purpose: isolate documentation and planning artifacts.

Likely files:

```txt
FOLDER_STRUCTURE.md
taxonomy.md
docs/EVIDENCE_LOG_SCHEMA.md
docs/EVAL_METRICS.md
docs/OBSERVABILITY.md
docs/SCHEMA_CONTRACT.md
docs/STATE_MACHINE.md
docs/journal/
docs/legacy/
docs/superpowers/plans/
missions/README.md
missions/active/
missions/completed/
```

Verification:

```powershell
git diff --check
```

Commit:

```powershell
git commit -m "docs: record WorkBridge mission mapping and taxonomy updates"
```

Done when:

- mission movement from active to completed is intentional
- FOLDER_STRUCTURE reflects new tracked paths
- journal accurately says what was confirmed versus planned

---

## Checkpoint 8: Local Helper Scripts Decision

Purpose: decide whether developer-local helpers belong in the repo.

Likely files:

```txt
scripts/codex_logged.ps1
scripts/workbridge_profile.ps1
```

Decision:

- If these are reusable team scripts, commit them with docs.
- If they are personal local helpers, add them to `.gitignore` or keep them unstaged.

Verification:

```powershell
git diff -- scripts/codex_logged.ps1 scripts/workbridge_profile.ps1
```

Possible commit:

```powershell
git commit -m "chore(dev): add local WorkBridge execution helpers"
```

---

## Final Verification

After all scoped commits are created:

```powershell
uv run pytest backend/tests
uv run python scripts/run_evals.py --dataset intent_router_cases
uv run python scripts/run_evals.py --dataset safety_guardrail_cases
uv run python scripts/run_evals.py --dataset workflow_e2e_cases
uv run python scripts/run_evals.py --dataset rag_retrieval_cases
npm run build
npm run test:run
git status --short
```

If `uv` cache permissions block normal execution, rerun the same `uv run ...` command with the approved elevated path and record that in the journal.

---

## PR Strategy After Splitting

Preferred order:

1. Agent runtime and guardrail acceptance
2. RAG source and metadata hardening
3. Document check and hiring agent connection
4. LLM judgment/report runtime
5. Backend API plumbing
6. Frontend API integration skeleton
7. Docs and legacy mapping

If this is a solo repo and review overhead matters, keep these as scoped commits in one branch first. Only split into multiple PRs if the remote branch review process actually benefits from it.

Do not open a PR until:

- each commit has a clear scope
- verification commands are recorded
- no unrelated generated/cache artifacts are staged
- `git status --short` only shows intentionally uncommitted local files, or is clean
