# Agent Output Aggregation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** WorkBridge의 인력 확보, 비자/서류, 다국어/소통 agent 결과를 직접 결합하지 않고 표준 output schema와 Aggregator node로 하나의 case output으로 수렴시킨다.

**Architecture:** 각 agent는 독립적으로 실행되고, `executor.py`는 agent별 표준 결과만 모은다. 새 `aggregator.py`가 checklist, missing inputs/documents, risk flags, evidence sources, approval required actions를 병합하고, `approval_gate.py`와 `final_response.py`는 이 aggregated output을 기준으로 동작한다.

**Tech Stack:** FastAPI backend, Python 3.12, Pydantic, pytest, WorkBridge Agent Runtime graph.

---

## 0. 배경과 결정

Notion `세 에이전트 수렴 아키텍처`의 핵심 결정은 "세 agent가 진짜 만나는 곳은 Aggregator + Human Approval"이다.

이 작업에서 하지 않는 것:

- `hiring_agent.py`, `visa_agent.py`, `contact_agent.py`를 하나의 거대 agent로 합치지 않는다.
- LangChain에게 routing, blocking, approval 최종권을 주지 않는다.
- 메시지 발송, 정부 포털 제출, 케이스 완료 처리를 자동 실행하지 않는다.
- agent별 raw output을 그대로 final response에 노출하지 않는다.

이 작업에서 하는 것:

- agent별 output schema를 고정한다.
- `executor.py`가 `agent_outputs`를 반환하게 한다.
- `aggregator.py`가 `aggregated_output`을 만든다.
- approval/final response/judgment input이 aggregated output을 참조하게 한다.
- 기존 `draft`, `drafts`, `tool_results`는 호환 필드로 유지한다.

---

## 1. 파일 구조

### Create

- `backend/app/agent_runtime/schemas/agent_output.py`
  - agent별 표준 output과 aggregated case output Pydantic schema.

- `backend/app/agent_runtime/graph/nodes/aggregator.py`
  - `execution["agent_outputs"]`를 읽어 하나의 `aggregated_output`으로 병합.

- `backend/tests/test_agent_aggregation.py`
  - schema, aggregator, workflow integration 테스트.

- `missions/active/014-agent-output-aggregation.md`
  - 공식 mission 파일.

### Modify

- `backend/app/agent_runtime/graph/nodes/executor.py`
  - agent별 결과를 `agent_outputs`에 표준 형태로 추가.
  - 기존 `drafts`, `draft`, `tool_results`는 깨지지 않게 유지.

- `backend/app/agent_runtime/graph/workflow.py`
  - `execute_plan()` 이후 `aggregate_agent_outputs()` 호출.
  - aggregator evidence event 추가.
  - result에 `aggregated_output` 포함.

- `backend/app/agent_runtime/graph/nodes/approval_gate.py`
  - aggregated output의 `approval_required_actions`를 우선 참조.

- `backend/app/agent_runtime/graph/nodes/final_response.py`
  - `aggregated_output` 중심 final response 생성.
  - 기존 `draft`와 `tool_results`는 호환 필드로 유지.

- `backend/tests/test_agent_workflow.py`
  - 기존 endpoint 테스트에 `aggregated_output` assertion 추가.

- `evals/datasets/workflow_e2e_cases.jsonl`
  - 필요하면 expected output에 `must_include_aggregated_output=true` 같은 runtime 검증 필드 추가.

- `scripts/run_evals.py`
  - workflow e2e eval에서 aggregated output 존재 여부를 검증.

- `missions/README.md`
  - active mission 목록에 014 추가.

- `FOLDER_STRUCTURE.md`
  - 새 plan과 active mission 파일 반영.

---

## 2. 표준 Agent Output 계약

모든 agent는 아래 구조를 따른다.

```json
{
  "agent_id": "workforce_agent",
  "status": "draft",
  "summary": "신규 고용 준비 초안을 생성했습니다.",
  "checklist": [],
  "required_documents": [],
  "missing_documents": [],
  "missing_inputs": [],
  "risk_flags": [],
  "evidence_sources": [],
  "approval_required_actions": [],
  "next_actions": [],
  "raw": {}
}
```

Aggregated output은 아래 구조를 따른다.

```json
{
  "case_summary": "신규 고용 준비 초안을 생성했습니다.",
  "agent_outputs": {},
  "combined_checklist": [],
  "required_documents": [],
  "missing_documents": [],
  "missing_inputs": [],
  "risk_flags": [],
  "evidence_sources": [],
  "approval_required": true,
  "approval_required_actions": [],
  "next_actions": []
}
```

---

### Task 1: Agent Output Schema 추가

**Files:**
- Create: `backend/app/agent_runtime/schemas/agent_output.py`
- Test: `backend/tests/test_agent_aggregation.py`

- [ ] **Step 1: Write the failing schema test**

Add this test to `backend/tests/test_agent_aggregation.py`.

```python
from app.agent_runtime.schemas.agent_output import AgentOutput, AggregatedCaseOutput


def test_agent_output_schema_defaults_are_safe() -> None:
    output = AgentOutput(agent_id="workforce_agent", summary="초안 생성")

    assert output.status == "draft"
    assert output.checklist == []
    assert output.approval_required_actions == []
    assert output.raw == {}


def test_aggregated_case_output_sets_approval_from_actions() -> None:
    aggregated = AggregatedCaseOutput(
        case_summary="검토 필요",
        approval_required_actions=[
            {
                "action_type": "send_message",
                "label": "근로자에게 메시지 발송",
                "reason": "외부 발송은 담당자 승인이 필요합니다.",
                "source_agent": "communication_agent",
            }
        ],
    )

    assert aggregated.approval_required is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py -q
```

Expected:

```txt
ModuleNotFoundError: No module named 'app.agent_runtime.schemas.agent_output'
```

- [ ] **Step 3: Implement schema**

Create `backend/app/agent_runtime/schemas/agent_output.py`.

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


AgentStatus = Literal["draft", "executed", "blocked", "mocked", "error"]


class EvidenceSourceRef(BaseModel):
    source_id: str
    chunk_id: str | None = None
    evidence_grade: str | None = None
    title: str | None = None


class AgentRiskFlag(BaseModel):
    type: str
    level: Literal["low", "medium", "high"] = "medium"
    reason: str
    source_agent: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class ApprovalRequiredAction(BaseModel):
    action_type: str
    label: str
    reason: str
    source_agent: str


class AgentOutput(BaseModel):
    agent_id: str
    status: AgentStatus = "draft"
    summary: str = ""
    checklist: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    risk_flags: list[AgentRiskFlag] = Field(default_factory=list)
    evidence_sources: list[EvidenceSourceRef] = Field(default_factory=list)
    approval_required_actions: list[ApprovalRequiredAction] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class AggregatedCaseOutput(BaseModel):
    case_summary: str = ""
    agent_outputs: dict[str, AgentOutput] = Field(default_factory=dict)
    combined_checklist: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    risk_flags: list[AgentRiskFlag] = Field(default_factory=list)
    evidence_sources: list[EvidenceSourceRef] = Field(default_factory=list)
    approval_required: bool = False
    approval_required_actions: list[ApprovalRequiredAction] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def set_approval_required_from_actions(self) -> "AggregatedCaseOutput":
        if self.approval_required_actions:
            self.approval_required = True
        return self
```

- [ ] **Step 4: Run schema test**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py -q
```

Expected:

```txt
2 passed
```

---

### Task 2: Aggregator Node 추가

**Files:**
- Create: `backend/app/agent_runtime/graph/nodes/aggregator.py`
- Modify: `backend/tests/test_agent_aggregation.py`

- [ ] **Step 1: Write failing aggregator tests**

Append to `backend/tests/test_agent_aggregation.py`.

```python
from app.agent_runtime.graph.nodes.aggregator import aggregate_agent_outputs


def test_aggregator_merges_agent_outputs_and_dedupes_lists() -> None:
    result = aggregate_agent_outputs(
        {
            "execution": {
                "agent_outputs": {
                    "workforce_agent": {
                        "agent_id": "workforce_agent",
                        "summary": "신규 고용 준비",
                        "checklist": ["사업장 정보 확인", "사업장 정보 확인"],
                        "missing_documents": ["고용허가 신청서"],
                        "risk_flags": [
                            {
                                "type": "missing_documents",
                                "level": "medium",
                                "reason": "필수 서류가 부족합니다.",
                                "source_agent": "workforce_agent",
                            }
                        ],
                    },
                    "communication_agent": {
                        "agent_id": "communication_agent",
                        "summary": "메시지 초안",
                        "approval_required_actions": [
                            {
                                "action_type": "send_message",
                                "label": "근로자 메시지 발송",
                                "reason": "외부 발송은 승인 필요",
                                "source_agent": "communication_agent",
                            }
                        ],
                    },
                }
            }
        }
    )

    assert result["case_summary"] == "신규 고용 준비 / 메시지 초안"
    assert result["combined_checklist"] == ["사업장 정보 확인"]
    assert result["missing_documents"] == ["고용허가 신청서"]
    assert result["approval_required"] is True
    assert result["approval_required_actions"][0]["action_type"] == "send_message"
    assert result["risk_flags"][0]["type"] == "missing_documents"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_aggregator_merges_agent_outputs_and_dedupes_lists -q
```

Expected:

```txt
ModuleNotFoundError: No module named 'app.agent_runtime.graph.nodes.aggregator'
```

- [ ] **Step 3: Implement aggregator**

Create `backend/app/agent_runtime/graph/nodes/aggregator.py`.

```python
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.schemas.agent_output import AgentOutput, AggregatedCaseOutput


def aggregate_agent_outputs(context: Mapping[str, Any]) -> dict[str, Any]:
    execution = context.get("execution") if isinstance(context.get("execution"), Mapping) else {}
    raw_outputs = execution.get("agent_outputs") if isinstance(execution.get("agent_outputs"), Mapping) else {}

    agent_outputs: dict[str, AgentOutput] = {}
    for agent_id, raw_output in raw_outputs.items():
        if not isinstance(raw_output, Mapping):
            continue
        output_data = dict(raw_output)
        output_data.setdefault("agent_id", str(agent_id))
        agent_outputs[str(agent_id)] = AgentOutput.model_validate(output_data)

    summaries = [output.summary for output in agent_outputs.values() if output.summary]
    aggregated = AggregatedCaseOutput(
        case_summary=" / ".join(summaries) if summaries else "검토할 agent output이 없습니다.",
        agent_outputs=agent_outputs,
        combined_checklist=_dedupe_flat([output.checklist for output in agent_outputs.values()]),
        required_documents=_dedupe_flat([output.required_documents for output in agent_outputs.values()]),
        missing_documents=_dedupe_flat([output.missing_documents for output in agent_outputs.values()]),
        missing_inputs=_dedupe_flat([output.missing_inputs for output in agent_outputs.values()]),
        risk_flags=[
            risk_flag
            for output in agent_outputs.values()
            for risk_flag in output.risk_flags
        ],
        evidence_sources=[
            evidence
            for output in agent_outputs.values()
            for evidence in output.evidence_sources
        ],
        approval_required_actions=[
            action
            for output in agent_outputs.values()
            for action in output.approval_required_actions
        ],
        next_actions=_dedupe_flat([output.next_actions for output in agent_outputs.values()]),
    )
    return aggregated.model_dump(mode="json")


def _dedupe_flat(groups: list[list[str]]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
    return result
```

- [ ] **Step 4: Run aggregator tests**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py -q
```

Expected:

```txt
3 passed
```

---

### Task 3: Executor가 표준 agent_outputs를 반환하게 변경

**Files:**
- Modify: `backend/app/agent_runtime/graph/nodes/executor.py`
- Modify: `backend/tests/test_agent_aggregation.py`

- [ ] **Step 1: Write failing executor test**

Append to `backend/tests/test_agent_aggregation.py`.

```python
from app.agent_runtime.graph.nodes.executor import execute_plan


def test_executor_returns_standard_agent_outputs() -> None:
    execution = execute_plan(
        {
            "plan": {
                "required_agents": ["workforce_agent", "visa_document_agent", "communication_agent"]
            },
            "case_type": "new_hiring",
            "current_state": "site_check",
            "input_state": {
                "visa_type": "E-9",
                "held_documents": ["passport"],
            },
        }
    )

    assert "agent_outputs" in execution
    assert execution["agent_outputs"]["workforce_agent"]["agent_id"] == "workforce_agent"
    assert execution["agent_outputs"]["visa_document_agent"]["status"] == "mocked"
    assert execution["agent_outputs"]["communication_agent"]["approval_required_actions"][0]["action_type"] == "send_message"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_executor_returns_standard_agent_outputs -q
```

Expected:

```txt
KeyError: 'agent_outputs'
```

- [ ] **Step 3: Modify executor**

In `backend/app/agent_runtime/graph/nodes/executor.py`, keep the current logic and add an `agent_outputs` dict.

Implementation rule:

- `workforce_agent` output wraps `build_hiring_draft()` result.
- `visa_document_agent` remains placeholder but uses standard schema.
- `communication_agent` remains `draft_only`, and adds `approval_required_actions`.
- `briefing_agent` remains placeholder.
- Existing `draft`, `drafts`, `tool_results` fields stay.

Expected output shape:

```python
agent_outputs["communication_agent"] = {
    "agent_id": "communication_agent",
    "status": "draft",
    "summary": "외부 메시지/전달 초안은 담당자 승인 후에만 실행됩니다.",
    "approval_required_actions": [
        {
            "action_type": "send_message",
            "label": "외부 메시지 또는 패키지 전달",
            "reason": "외부 발송/전달은 담당자 승인 이후에만 가능합니다.",
            "source_agent": "communication_agent",
        }
    ],
    "next_actions": ["담당자가 메시지 초안을 검토합니다."],
    "raw": tool_results["communication_agent"],
}
```

For `workforce_agent`, map document gap into standard fields:

```python
agent_outputs["workforce_agent"] = {
    "agent_id": "workforce_agent",
    "status": "draft",
    "summary": "신규 고용 준비 초안을 생성했습니다.",
    "checklist": draft.get("site_checklist", []),
    "required_documents": document_gap.get("output", {}).get("required_documents", []),
    "missing_documents": document_gap.get("output", {}).get("missing_documents", []),
    "missing_inputs": draft.get("questions_for_employer_or_partner", []),
    "risk_flags": [
        {
            "type": str(flag),
            "level": "medium",
            "reason": str(flag),
            "source_agent": "workforce_agent",
        }
        for flag in draft.get("risk_flags", [])
    ],
    "next_actions": draft.get("next_actions", []),
    "raw": draft,
}
```

- [ ] **Step 4: Run executor test**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_executor_returns_standard_agent_outputs -q
```

Expected:

```txt
1 passed
```

---

### Task 4: Workflow에 Aggregator Node 연결

**Files:**
- Modify: `backend/app/agent_runtime/graph/workflow.py`
- Modify: `backend/tests/test_agent_workflow.py`
- Modify: `backend/tests/test_agent_aggregation.py`

- [ ] **Step 1: Write failing workflow aggregation test**

Append to `backend/tests/test_agent_aggregation.py`.

```python
from app.services.agent_service import run_agent_request


def test_workflow_includes_aggregated_output_before_final_response() -> None:
    result = run_agent_request(
        {
            "request_id": "req_aggregation",
            "user_message": "E-9 신규 채용 준비하고 행정사에게 보낼 패키지도 준비해줘.",
            "case_type": "new_hiring",
            "input_state": {
                "visa_type": "E-9",
                "held_documents": ["passport"],
            },
        }
    )

    assert "aggregated_output" in result
    assert result["aggregated_output"]["approval_required"] is True
    assert "agent_outputs" in result["aggregated_output"]
    assert result["final_response"]["aggregated_output"]["approval_required"] is True
    assert any(event["agent_id"] == "aggregator" for event in result["evidence_events"])
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_workflow_includes_aggregated_output_before_final_response -q
```

Expected:

```txt
AssertionError: assert 'aggregated_output' in result
```

- [ ] **Step 3: Modify workflow**

In `backend/app/agent_runtime/graph/workflow.py`:

1. Import aggregator.

```python
from app.agent_runtime.graph.nodes.aggregator import aggregate_agent_outputs
```

2. After `execute_plan(...)` and its evidence event, call aggregator.

```python
    aggregated_output = aggregate_agent_outputs(
        {
            "execution": execution,
            "case_type": case_type,
            "current_state": current_state,
            "detected_intents": detected_intents,
        }
    )
    append_event(
        evidence_events,
        work_item_id=work_item_id,
        agent_id="aggregator",
        action_type="aggregate",
        event_type="tool_executed",
        input_data={"agent_ids": list(execution.get("agent_outputs", {}).keys())},
        output_data={
            "approval_required": aggregated_output.get("approval_required", False),
            "risk_flag_count": len(aggregated_output.get("risk_flags", [])),
            "missing_document_count": len(aggregated_output.get("missing_documents", [])),
        },
    )
```

3. Pass `aggregated_output` into approval and final response context.

```python
    approval = evaluate_approval(
        {
            **incoming,
            "execution": execution,
            "aggregated_output": aggregated_output,
            "approval_required": aggregated_output.get("approval_required", True),
        }
    )
```

4. Include in result.

```python
        "aggregated_output": aggregated_output,
```

- [ ] **Step 4: Run workflow aggregation test**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_workflow_includes_aggregated_output_before_final_response -q
```

Expected:

```txt
1 passed
```

---

### Task 5: Approval Gate를 Aggregated Output 기준으로 보강

**Files:**
- Modify: `backend/app/agent_runtime/graph/nodes/approval_gate.py`
- Modify: `backend/tests/test_agent_aggregation.py`

- [ ] **Step 1: Write failing approval test**

Append to `backend/tests/test_agent_aggregation.py`.

```python
from app.agent_runtime.graph.nodes.approval_gate import evaluate_approval


def test_approval_gate_uses_aggregated_required_actions() -> None:
    approval = evaluate_approval(
        {
            "human_approved": False,
            "approval_required": False,
            "aggregated_output": {
                "approval_required": True,
                "approval_required_actions": [
                    {
                        "action_type": "send_message",
                        "label": "메시지 발송",
                        "reason": "외부 발송",
                        "source_agent": "communication_agent",
                    }
                ],
            },
        }
    )

    assert approval["required"] is True
    assert approval["status"] == "PENDING"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_approval_gate_uses_aggregated_required_actions -q
```

Expected:

```txt
AssertionError: assert False is True
```

- [ ] **Step 3: Modify approval gate**

Update `backend/app/agent_runtime/graph/nodes/approval_gate.py` so `aggregated_output.approval_required` has priority.

Expected logic:

```python
aggregated = context.get("aggregated_output") if isinstance(context.get("aggregated_output"), dict) else {}
aggregated_required = bool(
    aggregated.get("approval_required")
    or aggregated.get("approval_required_actions")
)
required = bool(context.get("approval_required", True) or aggregated_required)
```

Return shape stays compatible:

```python
{
    "required": required,
    "status": "APPROVED" if required and human_approved else "PENDING" if required else "NOT_REQUIRED",
    "human_approved": human_approved,
}
```

- [ ] **Step 4: Run approval test**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_approval_gate_uses_aggregated_required_actions -q
```

Expected:

```txt
1 passed
```

---

### Task 6: Final Response를 Aggregated Output 중심으로 변경

**Files:**
- Modify: `backend/app/agent_runtime/graph/nodes/final_response.py`
- Modify: `backend/tests/test_agent_aggregation.py`

- [ ] **Step 1: Write failing final response test**

Append to `backend/tests/test_agent_aggregation.py`.

```python
from app.agent_runtime.graph.nodes.final_response import build_final_response


def test_final_response_prefers_aggregated_output() -> None:
    response = build_final_response(
        {
            "case_type": "new_hiring",
            "current_state": "site_check",
            "next_state": "candidate_intake",
            "approval": {"status": "PENDING", "required": True},
            "execution": {"draft": {"legacy": True}, "tool_results": {"quota_tool": {"status": "SUCCESS"}}},
            "aggregated_output": {
                "case_summary": "통합 검토 결과",
                "approval_required": True,
                "combined_checklist": ["사업장 정보 확인"],
                "missing_documents": ["고용허가 신청서"],
            },
        }
    )

    assert response["aggregated_output"]["case_summary"] == "통합 검토 결과"
    assert response["draft"] == {"legacy": True}
    assert response["tool_results"]["quota_tool"]["status"] == "SUCCESS"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_final_response_prefers_aggregated_output -q
```

Expected:

```txt
KeyError: 'aggregated_output'
```

- [ ] **Step 3: Modify final response**

In `backend/app/agent_runtime/graph/nodes/final_response.py`, include:

```python
aggregated_output = context.get("aggregated_output")
if aggregated_output:
    response["aggregated_output"] = aggregated_output
```

Keep existing fields:

- `draft`
- `tool_results`
- `judgment_report`
- `approval_status`
- `approval_required`

- [ ] **Step 4: Run final response test**

Run:

```powershell
uv run pytest backend/tests/test_agent_aggregation.py::test_final_response_prefers_aggregated_output -q
```

Expected:

```txt
1 passed
```

---

### Task 7: Eval Runner에 Aggregated Output 검증 추가

**Files:**
- Modify: `evals/datasets/workflow_e2e_cases.jsonl`
- Modify: `scripts/run_evals.py`
- Test: `backend/tests/test_eval_runner.py`

- [ ] **Step 1: Add expected field to workflow E2E cases**

For workflow cases that should run full agent flow, add:

```json
"must_include_aggregated_output": true
```

For blocked cases, use:

```json
"must_include_aggregated_output": false
```

- [ ] **Step 2: Write eval runner test**

Add to `backend/tests/test_eval_runner.py`:

```python
from scripts.run_evals import evaluate_workflow_case


def test_workflow_eval_checks_aggregated_output_presence() -> None:
    issues = evaluate_workflow_case(
        {
            "id": "aggregation_eval",
            "input": {
                "request_id": "aggregation_eval",
                "user_message": "E-9 신규 채용 준비해줘.",
                "case_type": "new_hiring",
            },
            "expected": {
                "must_include_aggregated_output": True,
            },
        }
    )

    assert issues == []
```

- [ ] **Step 3: Update eval runner**

In `scripts/run_evals.py`, inside workflow case evaluation:

```python
must_include = expected.get("must_include_aggregated_output")
if must_include is True and "aggregated_output" not in result:
    issues.append("missing aggregated_output")
if must_include is False and "aggregated_output" in result and result.get("status") == "blocked":
    issues.append("blocked case should not require aggregated_output")
```

- [ ] **Step 4: Run eval runner tests**

Run:

```powershell
uv run pytest backend/tests/test_eval_runner.py -q
uv run python scripts/run_evals.py --dataset workflow_e2e_cases --strict
```

Expected:

```txt
test_eval_runner.py passed
workflow_e2e_cases: 2 cases, 0 issues
```

---

### Task 8: Full Regression

**Files:**
- All touched files.

- [ ] **Step 1: Run aggregation-focused tests**

```powershell
uv run pytest backend/tests/test_agent_aggregation.py -q
```

Expected:

```txt
all tests passed
```

- [ ] **Step 2: Run agent workflow tests**

```powershell
uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_approvals.py backend/tests/test_evidence.py backend/tests/test_guardrails.py -q
```

Expected:

```txt
all tests passed
```

- [ ] **Step 3: Run all backend tests**

```powershell
uv run pytest backend/tests
```

Expected:

```txt
passed
```

- [ ] **Step 4: Run evals**

```powershell
uv run python scripts/run_evals.py --dataset workflow_e2e_cases --strict
uv run python scripts/run_evals.py --dataset safety_guardrail_cases --strict
uv run python scripts/run_evals.py --dataset langchain_judgment_cases --strict
```

Expected:

```txt
0 issues
```

- [ ] **Step 5: Manual API smoke test**

Start server:

```powershell
uv run uvicorn app.main:app --app-dir backend --reload --port 8000
```

In another shell:

```powershell
$body = @{
  request_id = "manual_aggregation_001"
  user_message = "E-9 신규 채용 준비하고 행정사에게 보낼 패키지도 준비해줘."
  case_type = "new_hiring"
  runtime_mode = "langchain_judgment"
  input_state = @{
    visa_type = "E-9"
    held_documents = @("passport")
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/agent/run" `
  -ContentType "application/json" `
  -Body $body
```

Expected response contains:

- `aggregated_output`
- `aggregated_output.agent_outputs.workforce_agent`
- `aggregated_output.approval_required = true`
- `approval.status = PENDING`
- `final_response.aggregated_output`
- Evidence event with `agent_id = aggregator`

---

## Completion Criteria

- `executor.py` returns `agent_outputs` without breaking legacy `draft`, `drafts`, `tool_results`.
- `aggregator.py` creates a single `aggregated_output`.
- `approval_gate.py` respects `aggregated_output.approval_required_actions`.
- `final_response.py` includes `aggregated_output`.
- Workflow response includes both `execution.agent_outputs` and top-level `aggregated_output`.
- Blocked requests still stop before judgment/report execution.
- Message sending, government submission, handoff, export remain approval pending or blocked.
- Backend tests pass.
- Workflow eval detects missing aggregated output.

---

## Commit Plan

Commit in small units:

```powershell
git add backend/app/agent_runtime/schemas/agent_output.py backend/tests/test_agent_aggregation.py
git commit -m "feat(agent): add standard agent output schema"

git add backend/app/agent_runtime/graph/nodes/aggregator.py backend/tests/test_agent_aggregation.py
git commit -m "feat(agent): aggregate multi-agent outputs"

git add backend/app/agent_runtime/graph/nodes/executor.py backend/app/agent_runtime/graph/workflow.py backend/app/agent_runtime/graph/nodes/approval_gate.py backend/app/agent_runtime/graph/nodes/final_response.py backend/tests/test_agent_aggregation.py backend/tests/test_agent_workflow.py
git commit -m "feat(agent): wire aggregation into runtime"

git add scripts/run_evals.py evals/datasets/workflow_e2e_cases.jsonl backend/tests/test_eval_runner.py
git commit -m "test(agent): enforce aggregated workflow output in evals"
```

---

## Self-Review

- Spec coverage: Notion의 Data/Schema/Workflow/Output 수렴 원칙 중 이번 plan은 Workflow/Output 수렴을 구현한다. Data persistence는 `015` 후보로 분리한다.
- Placeholder scan: no `TBD`, no open-ended "handle later" step. Production provider, DB persistence, frontend real build는 scope 밖으로 명시했다.
- Type consistency: `AgentOutput`, `AggregatedCaseOutput`, `approval_required_actions`, `aggregated_output` 이름을 모든 task에서 동일하게 사용한다.
