# RAG Source And Workforce Agent Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand WorkBridge's official RAG corpus and close the workforce-agent path from official evidence to document gap calculation, hiring draft, judgment JSON, and report output.

**Architecture:** Keep the current deterministic runtime as the safety boundary. RAG provides official evidence packages, CSV/rule tools calculate current readiness and missing documents, fake/provider-agnostic LLM judgment turns evidence into strict JSON, and reports remain draft-only until human approval.

**Tech Stack:** Python 3.12, FastAPI backend modules, Pydantic, JSONL/CSV seed data, existing lexical RAG retriever, pytest, `scripts/ingest_rag_docs.py`, `scripts/run_evals.py`.

---

## Current Baseline

- RAG chunks exist at `data-pipeline/processed/chunks/all_chunks.jsonl`.
- RAG retrieval eval exists at `evals/datasets/rag_retrieval_cases.jsonl`, currently 5 cases.
- Official raw source count is currently 6 in `data-pipeline/raw/source_manifest.json`.
- `backend/app/agent_runtime/rag/evidence_package.py` exists and tests pass.
- `backend/app/agent_runtime/llm/` exists with fake judgment client, parser, prompt builder, and chain.
- `backend/app/agent_runtime/reporting/` exists with risk/report generation.
- `backend/app/agent_runtime/tools/document_check_tool.py` is empty and is the first implementation gap.
- `backend/app/agent_runtime/agents/hiring_agent.py` creates a draft but does not yet calculate missing documents from `document_requirements.csv` or attach an Evidence Package.

## Source Targets

Add source manifest rows and seed docs until the MVP has at least 20 source records across these buckets:

- Laws/forms: Immigration Act, Enforcement Decree, Enforcement Rule, Foreign Workers Employment Act, its Enforcement Decree, its Enforcement Rule, integrated application form, employment change report form, workplace information change form.
- EPS/employment procedures: employment permit system overview, employer employment procedure, allowed industries, employer scoring indicators, employment permit application guide, employment permit extension flow.
- Gov24/HiKorea: stay period extension permit, foreigner residence change report, visa/stay guide references.
- Safety/templates: KOSHA multilingual safety guide, safety signs, document request message templates, safety notice templates, expert handoff templates.

Use answer evidence grades only as defined in `docs/RAG_STRATEGY.md`: A, B, and E can support generated drafts; C/D/F cannot support official claims.

---

### Task 1: Add Document Gap Tool

**Files:**
- Modify: `backend/app/agent_runtime/tools/document_check_tool.py`
- Test: `backend/tests/test_document_check_tool.py`

- [ ] **Step 1: Write failing tests for required document calculation**

Create `backend/tests/test_document_check_tool.py`:

```python
from pathlib import Path

from app.agent_runtime.tools.document_check_tool import calculate_missing_documents


def test_calculate_missing_documents_for_new_hiring_e9() -> None:
    result = calculate_missing_documents(
        {
            "case_type": "new_hiring",
            "visa_type": "E-9",
            "held_documents": ["passport", "health_certificate"],
        },
        requirements_path=Path("data-pipeline/seed/document_requirements.csv"),
    )

    assert result["tool_name"] == "calculate_missing_documents"
    assert result["tool_grade"] == "SAFE_CALCULATE"
    assert result["status"] == "SUCCESS"
    assert result["approval_required"] is False
    assert result["output"]["case_type"] == "new_hiring"
    assert result["output"]["visa_type"] == "E-9"
    assert "criminal_record" in result["output"]["missing_documents"]
    assert "passport" not in result["output"]["missing_documents"]
    assert result["risk_flags"] == ["missing_required_documents"]


def test_calculate_missing_documents_requires_case_type() -> None:
    result = calculate_missing_documents(
        {"visa_type": "E-9", "held_documents": []},
        requirements_path=Path("data-pipeline/seed/document_requirements.csv"),
    )

    assert result["status"] == "FAILED"
    assert result["error"] == "case_type is required"
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
uv run pytest backend/tests/test_document_check_tool.py -v
```

Expected: import failure because `calculate_missing_documents` is not defined.

- [ ] **Step 3: Implement the tool**

Replace `backend/app/agent_runtime/tools/document_check_tool.py` with:

```python
from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


DEFAULT_REQUIREMENTS_PATH = Path("data-pipeline/seed/document_requirements.csv")


def calculate_missing_documents(
    payload: Mapping[str, Any],
    *,
    requirements_path: str | Path = DEFAULT_REQUIREMENTS_PATH,
) -> dict[str, Any]:
    case_type = str(payload.get("case_type") or "").strip()
    visa_type = str(payload.get("visa_type") or payload.get("visa") or "E-9").strip()
    held_documents = _normalize_documents(payload.get("held_documents") or payload.get("documents") or [])

    if not case_type:
        return _failed("case_type is required", {"case_type": case_type, "visa_type": visa_type})
    if not visa_type:
        return _failed("visa_type is required", {"case_type": case_type, "visa_type": visa_type})

    requirements = _load_required_documents(Path(requirements_path), case_type=case_type, visa_type=visa_type)
    missing = sorted(doc for doc in requirements if doc not in held_documents)
    risk_flags = ["missing_required_documents"] if missing else []

    return {
        "tool_name": "calculate_missing_documents",
        "tool_grade": "SAFE_CALCULATE",
        "status": "SUCCESS",
        "input_snapshot": {
            "case_type": case_type,
            "visa_type": visa_type,
            "held_documents": sorted(held_documents),
        },
        "output": {
            "case_type": case_type,
            "visa_type": visa_type,
            "required_documents": sorted(requirements),
            "held_documents": sorted(held_documents),
            "missing_documents": missing,
        },
        "citations": sorted(requirements.values()),
        "risk_flags": risk_flags,
        "approval_required": False,
        "error": None,
    }


def _load_required_documents(path: Path, *, case_type: str, visa_type: str) -> dict[str, str]:
    requirements: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("case_type") != case_type:
                continue
            if row.get("visa_type") != visa_type:
                continue
            if str(row.get("required", "")).lower() != "true":
                continue
            doc = str(row.get("required_doc") or "").strip()
            source_id = str(row.get("source_id") or "").strip()
            if doc:
                requirements[doc] = source_id
    return requirements


def _normalize_documents(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        return {str(key) for key, present in value.items() if bool(present)}
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return {str(item) for item in value if str(item)}
    return set()


def _failed(error: str, input_snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool_name": "calculate_missing_documents",
        "tool_grade": "SAFE_CALCULATE",
        "status": "FAILED",
        "input_snapshot": input_snapshot,
        "output": {},
        "citations": [],
        "risk_flags": [],
        "approval_required": False,
        "error": error,
    }
```

- [ ] **Step 4: Run the tool tests**

Run:

```bash
uv run pytest backend/tests/test_document_check_tool.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/agent_runtime/tools/document_check_tool.py backend/tests/test_document_check_tool.py
git commit -m "feat: add document gap calculation tool"
```

---

### Task 2: Connect Hiring Agent To Document Requirements

**Files:**
- Modify: `backend/app/agent_runtime/agents/hiring_agent.py`
- Modify: `backend/app/agent_runtime/graph/nodes/executor.py`
- Test: `backend/tests/test_agent_workflow.py`

- [ ] **Step 1: Add a failing workflow assertion**

Append this test to `backend/tests/test_agent_workflow.py`:

```python
def test_new_hiring_includes_document_gap_result() -> None:
    result = run_workflow(
        {
            "request_id": "req_document_gap",
            "user_message": "E-9 신규 채용 준비해줘.",
            "case_type": "new_hiring",
            "input_state": {
                "company_id": "company_001",
                "requested_headcount": 3,
                "visa_type": "E-9",
                "held_documents": ["passport"],
            },
        }
    )

    doc_gap = result["execution"]["tool_results"]["document_check_tool"]
    assert doc_gap["status"] == "SUCCESS"
    assert "health_certificate" in doc_gap["output"]["missing_documents"]
    assert "criminal_record" in doc_gap["output"]["missing_documents"]
    assert result["execution"]["draft"]["document_gap"]["missing_documents"] == doc_gap["output"]["missing_documents"]
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
uv run pytest backend/tests/test_agent_workflow.py::test_new_hiring_includes_document_gap_result -v
```

Expected: `document_check_tool` key is missing.

- [ ] **Step 3: Wire document gap into executor**

Modify `backend/app/agent_runtime/graph/nodes/executor.py`:

```python
from app.agent_runtime.tools.document_check_tool import calculate_missing_documents
```

Inside the `if "workforce_agent" in required_agents:` block, after `quota_tool`:

```python
        document_gap = calculate_missing_documents(
            {
                "case_type": case_type,
                "visa_type": input_state.get("visa_type") or "E-9",
                "held_documents": input_state.get("held_documents") or input_state.get("documents") or [],
            }
        )
        tool_results["document_check_tool"] = document_gap
        if isinstance(draft, dict):
            draft["document_gap"] = {
                "required_documents": document_gap.get("output", {}).get("required_documents", []),
                "missing_documents": document_gap.get("output", {}).get("missing_documents", []),
                "citations": document_gap.get("citations", []),
            }
```

- [ ] **Step 4: Run the workflow test**

Run:

```bash
uv run pytest backend/tests/test_agent_workflow.py::test_new_hiring_includes_document_gap_result -v
```

Expected: pass.

- [ ] **Step 5: Run related tests**

Run:

```bash
uv run pytest backend/tests/test_document_check_tool.py backend/tests/test_agent_workflow.py -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/agent_runtime/agents/hiring_agent.py backend/app/agent_runtime/graph/nodes/executor.py backend/tests/test_agent_workflow.py
git commit -m "feat: connect hiring workflow to document gaps"
```

---

### Task 3: Rework RAG Source Manifest And Metadata Audit

**Files:**
- Modify: `data-pipeline/raw/source_manifest.json`
- Modify: `data-pipeline/seed/sample_policy_docs.jsonl`
- Modify: `backend/tests/test_rag_indexing.py`
- Create: `backend/tests/test_rag_source_manifest.py`

- [ ] **Step 1: Add source manifest coverage tests**

Create `backend/tests/test_rag_source_manifest.py`:

```python
import json
from pathlib import Path


def test_source_manifest_has_minimum_mvp_sources() -> None:
    manifest = json.loads(Path("data-pipeline/raw/source_manifest.json").read_text(encoding="utf-8"))
    sources = manifest["sources"]

    assert len(sources) >= 20
    assert {source["source_id"] for source in sources} >= {
        "eps_employer_process_001",
        "eps_allowed_industries_001",
        "gov24_stay_extension_001",
        "law_foreign_worker_act_001",
        "kosha_multilingual_safety_001",
    }


def test_source_manifest_rows_have_metadata_contract() -> None:
    manifest = json.loads(Path("data-pipeline/raw/source_manifest.json").read_text(encoding="utf-8"))
    required = {"source_id", "title", "official_url", "publisher", "source_type", "doc_type", "evidence_grade"}

    for source in manifest["sources"]:
        missing = required - set(source)
        assert not missing, f"{source.get('source_id')} missing {sorted(missing)}"
        assert source["evidence_grade"] in {"A", "B", "C", "D", "E", "F"}
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
uv run pytest backend/tests/test_rag_source_manifest.py -v
```

Expected: source count and metadata field failures.

- [ ] **Step 3: Expand manifest rows**

Update `data-pipeline/raw/source_manifest.json` so each row includes the required metadata fields. Use current official URLs from:

- `https://www.law.go.kr/lsInfoP.do?lsId=009542`
- `https://www.eps.go.kr/eo/EmployJobProc.eo?tabGb=01`
- `https://www.eps.go.kr/eo/EmployPerSystem.eo`
- `https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=12700000097`

Add placeholder source rows only when actual raw files are not collected yet, but mark them:

```json
{
  "source_id": "gov24_stay_extension_001",
  "title": "체류기간연장허가 민원 안내",
  "official_url": "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=12700000097",
  "saved_path": null,
  "downloaded_format": null,
  "collection_status": "planned",
  "publisher": "정부24",
  "source_type": "official_procedure",
  "doc_type": "procedure",
  "evidence_grade": "A"
}
```

- [ ] **Step 4: Run source manifest tests**

Run:

```bash
uv run pytest backend/tests/test_rag_source_manifest.py -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add data-pipeline/raw/source_manifest.json backend/tests/test_rag_source_manifest.py
git commit -m "docs: expand RAG source manifest contract"
```

---

### Task 4: Normalize Chunk Metadata Contract

**Files:**
- Modify: `data-pipeline/ingest.py`
- Modify: `backend/app/agent_runtime/rag/chunking.py`
- Test: `backend/tests/test_rag_indexing.py`

- [ ] **Step 1: Add metadata audit test**

Append this test to `backend/tests/test_rag_indexing.py`:

```python
def test_all_chunks_have_complete_metadata_contract() -> None:
    import json
    from pathlib import Path

    required = {
        "source_id",
        "title",
        "publisher",
        "source_type",
        "url",
        "retrieved_at",
        "effective_date",
        "doc_type",
        "mission_agent",
        "visa_type",
        "country",
        "industry",
        "risk_level",
        "evidence_grade",
    }

    for line_no, line in enumerate(Path("data-pipeline/processed/chunks/all_chunks.jsonl").read_text(encoding="utf-8").splitlines(), start=1):
        row = json.loads(line)
        metadata = row.get("metadata", {})
        missing = required - set(metadata)
        assert not missing, f"line {line_no} missing metadata {sorted(missing)}"
        assert metadata["evidence_grade"] in {"A", "B", "C", "D", "E", "F"}
        assert isinstance(metadata["mission_agent"], list)
        assert isinstance(metadata["visa_type"], list)
```

- [ ] **Step 2: Run the audit and confirm current gaps**

Run:

```bash
uv run pytest backend/tests/test_rag_indexing.py::test_all_chunks_have_complete_metadata_contract -v
```

Expected: fail if any chunk metadata is incomplete.

- [ ] **Step 3: Update ingest normalization**

In `data-pipeline/ingest.py`, centralize metadata defaults:

```python
def normalize_metadata(metadata: dict[str, object]) -> dict[str, object]:
    return {
        "source_id": metadata.get("source_id"),
        "title": metadata.get("title"),
        "publisher": metadata.get("publisher"),
        "source_type": metadata.get("source_type"),
        "url": metadata.get("url") or metadata.get("official_url") or "",
        "retrieved_at": metadata.get("retrieved_at"),
        "effective_date": metadata.get("effective_date"),
        "doc_type": metadata.get("doc_type"),
        "mission_agent": _as_list(metadata.get("mission_agent") or ["workforce_agent"]),
        "visa_type": _as_list(metadata.get("visa_type") or ["E-9"]),
        "country": _as_list(metadata.get("country") or ["ALL"]),
        "industry": _as_list(metadata.get("industry") or ["ALL"]),
        "risk_level": metadata.get("risk_level") or "medium",
        "evidence_grade": str(metadata.get("evidence_grade") or "F").upper(),
    }


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]
```

Call `normalize_metadata(...)` before writing every chunk row.

- [ ] **Step 4: Rebuild chunks**

Run:

```bash
uv run python scripts/ingest_rag_docs.py
```

Expected: regenerated `data-pipeline/processed/chunks/*.jsonl`.

- [ ] **Step 5: Run metadata and RAG tests**

Run:

```bash
uv run pytest backend/tests/test_rag_indexing.py backend/tests/test_rag_eval_dataset.py -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add data-pipeline/ingest.py backend/app/agent_runtime/rag/chunking.py backend/tests/test_rag_indexing.py data-pipeline/processed/chunks
git commit -m "feat: normalize RAG chunk metadata contract"
```

---

### Task 5: Expand Retrieval Eval From 5 To At Least 20 Cases

**Files:**
- Modify: `evals/datasets/rag_retrieval_cases.jsonl`
- Test: `backend/tests/test_rag_eval_dataset.py`

- [ ] **Step 1: Add dataset size and bucket tests**

Append this test to `backend/tests/test_rag_eval_dataset.py`:

```python
def test_rag_retrieval_cases_cover_mvp_buckets() -> None:
    import json
    from pathlib import Path

    rows = [
        json.loads(line)
        for line in Path("evals/datasets/rag_retrieval_cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) >= 20
    joined = "\n".join(row["input"] for row in rows)
    for keyword in ["신규 채용", "고용허가", "허용업종", "체류기간", "고용변동", "여권", "안전교육", "메시지"]:
        assert keyword in joined
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
uv run pytest backend/tests/test_rag_eval_dataset.py::test_rag_retrieval_cases_cover_mvp_buckets -v
```

Expected: fail because current dataset has 5 rows.

- [ ] **Step 3: Add at least 15 new cases**

Add cases covering:

```jsonl
{"id":"rag-006","input":"E-9 고용허가 신청 전에 내국인 구인노력 절차 근거 찾아줘","expected_source_ids":["eps_employer_process_001"],"answer_evidence_only":true}
{"id":"rag-007","input":"E-9 허용업종은 어디서 확인해야 해?","expected_source_ids":["eps_allowed_industries_001"],"answer_evidence_only":true}
{"id":"rag-008","input":"외국인근로자 고용변동 신고서 필드 근거 찾아줘","expected_source_ids":["law_form_employment_change_001"],"answer_evidence_only":true}
{"id":"rag-009","input":"체류기간 연장할 때 여권과 외국인등록증 근거 찾아줘","expected_source_ids":["gov24_stay_extension_001"],"answer_evidence_only":true}
{"id":"rag-010","input":"E-9 체류기간 연장에 고용허가서와 근로계약서가 필요한지 근거 찾아줘","expected_source_ids":["gov24_stay_extension_001"],"answer_evidence_only":true}
```

Continue with safety, templates, workplace change, and handoff package cases until the file has at least 20 rows.

- [ ] **Step 4: Run retrieval eval**

Run:

```bash
uv run python scripts/run_evals.py --dataset rag_retrieval_cases --strict
```

Expected: `Total issues: 0`.

- [ ] **Step 5: Commit**

```bash
git add evals/datasets/rag_retrieval_cases.jsonl backend/tests/test_rag_eval_dataset.py
git commit -m "test: expand RAG retrieval eval coverage"
```

---

### Task 6: Build Evidence Package Into Judgment Runtime

**Files:**
- Modify: `backend/app/agent_runtime/graph/workflow.py`
- Test: `backend/tests/test_agent_workflow.py`
- Test: `backend/tests/test_evidence.py`

- [ ] **Step 1: Add failing runtime test**

Append this test to `backend/tests/test_agent_workflow.py`:

```python
def test_langchain_judgment_runtime_uses_rag_evidence_package() -> None:
    result = run_workflow(
        {
            "request_id": "req_rag_judgment",
            "runtime_mode": "langchain_judgment",
            "user_message": "E-9 신규 채용 고용허가 절차 근거로 판단 리포트 만들어줘.",
            "case_type": "new_hiring",
            "input_state": {"company_id": "company_001", "requested_headcount": 3},
        }
    )

    assert result["judgment"]["evidence_summary"]
    event_types = [event["event_type"] for event in result["evidence_events"]]
    assert "rag_retrieved" in event_types
    assert result["judgment"]["evidence_summary"][0]["source_id"] != "workflow_runtime_context"
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
uv run pytest backend/tests/test_agent_workflow.py::test_langchain_judgment_runtime_uses_rag_evidence_package -v
```

Expected: fails because workflow currently uses `_default_evidence_package`.

- [ ] **Step 3: Build evidence package before fake judgment**

In `backend/app/agent_runtime/graph/workflow.py`, import:

```python
from pathlib import Path
from app.agent_runtime.rag.evidence_package import build_evidence_package
```

Replace `_default_evidence_package(...)` usage with:

```python
            evidence_package = build_evidence_package(
                request_id=work_item_id,
                query=str(incoming.get("user_message") or ""),
                case_type=case_type,
                chunk_path=Path("data-pipeline/processed/chunks/all_chunks.jsonl"),
                top_k=3,
                answer_evidence_only=True,
            )
```

Append evidence event:

```python
        append_event(
            evidence_events,
            work_item_id=work_item_id,
            agent_id="rag_retriever",
            action_type="retrieve",
            event_type="rag_retrieved",
            input_data={"query": evidence_package["query"], "case_type": case_type},
            output_data={
                "status": evidence_package["status"],
                "source_ids": [chunk["source_id"] for chunk in evidence_package["retrieved_chunks"]],
            },
        )
```

- [ ] **Step 4: Make fake judgment reflect evidence**

Change `_default_judgment_json(...)` signature to accept `evidence_package: dict[str, Any]`, then build `evidence_summary` from retrieved chunks:

```python
    evidence_summary = [
        {
            "claim": chunk["text"][:120],
            "source_id": chunk["source_id"],
            "evidence_grade": chunk["evidence_grade"],
        }
        for chunk in evidence_package.get("retrieved_chunks", [])
    ] or [
        {
            "claim": "공식 근거가 충분하지 않아 담당자 검토가 필요합니다.",
            "source_id": "insufficient_evidence",
            "evidence_grade": "E",
        }
    ]
```

- [ ] **Step 5: Run workflow and evidence tests**

Run:

```bash
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_evidence.py -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/agent_runtime/graph/workflow.py backend/tests/test_agent_workflow.py backend/tests/test_evidence.py
git commit -m "feat: use RAG evidence package in judgment runtime"
```

---

### Task 7: Verification Gate

**Files:**
- No source files unless failures reveal defects.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
uv run pytest backend/tests/test_document_check_tool.py backend/tests/test_evidence_package.py backend/tests/test_rag_indexing.py backend/tests/test_rag_eval_dataset.py backend/tests/test_llm_judgment_chain.py backend/tests/test_report_generation.py backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py backend/tests/test_evidence.py
```

Expected: all pass.

- [ ] **Step 2: Run evals**

Run:

```bash
uv run python scripts/run_evals.py --dataset rag_retrieval_cases --strict
uv run python scripts/run_evals.py --dataset safety_guardrail_cases --strict
uv run python scripts/run_evals.py --dataset workflow_e2e_cases --strict
```

Expected: all report `Total issues: 0`.

- [ ] **Step 3: Check dirty tree scope**

Run:

```bash
git status --short
```

Expected: only files from this plan changed.

---

## Mission Boundary

- Mission 002 should be re-opened or superseded by a hardening sub-mission for official source expansion and metadata audit.
- Mission 008 remains completed, but Task 6 strengthens actual runtime usage of Evidence Package.
- Mission 009/010/011 remain the judgment/report/runtime contract layer.
- Mission 012 LangChain adapter should wait until Tasks 1-7 pass.
- Mission 013 real provider should wait until Mission 012 has fake tests and no network calls in CI.

## Self-Review

- Spec coverage: covers document gap calculation, hiring draft connection, official source expansion, chunk metadata normalization, retrieval eval expansion, evidence package runtime use, and verification.
- Placeholder scan: no implementation step relies on TBD or unspecified behavior.
- Type consistency: tool responses follow `docs/TOOL_CONTRACT.md`; evidence grades follow `docs/RAG_STRATEGY.md`; workflow event names follow `docs/EVIDENCE_LOG_SCHEMA.md`.
