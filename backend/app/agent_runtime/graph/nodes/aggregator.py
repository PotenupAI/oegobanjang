from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.schemas.agent_output import AgentOutput, AggregatedCaseOutput


def aggregate_agent_outputs(context: Mapping[str, Any]) -> dict[str, Any]:
    execution = context.get("execution") if isinstance(context.get("execution"), Mapping) else {}
    raw_outputs = execution.get("agent_outputs") if isinstance(execution.get("agent_outputs"), Mapping) else {}
    agent_outputs = {
        str(agent_id): _coerce_agent_output(output)
        for agent_id, output in raw_outputs.items()
    }

    case_summary = _case_summary(agent_outputs)
    aggregated = AggregatedCaseOutput(
        case_summary=case_summary,
        agent_outputs=agent_outputs,
        combined_checklist=_dedupe_list(
            item
            for output in agent_outputs.values()
            for item in output.checklist
        ),
        required_documents=_dedupe_list(
            item
            for output in agent_outputs.values()
            for item in output.required_documents
        ),
        missing_documents=_dedupe_list(
            item
            for output in agent_outputs.values()
            for item in output.missing_documents
        ),
        missing_inputs=_dedupe_list(
            item
            for output in agent_outputs.values()
            for item in output.missing_inputs
        ),
        risk_flags=[
            flag
            for output in agent_outputs.values()
            for flag in output.risk_flags
        ],
        evidence_sources=_dedupe_evidence_sources(
            source
            for output in agent_outputs.values()
            for source in output.evidence_sources
        ),
        approval_required_actions=[
            action
            for output in agent_outputs.values()
            for action in output.approval_required_actions
        ],
        next_actions=_dedupe_list(
            item
            for output in agent_outputs.values()
            for item in output.next_actions
        ),
    )
    return aggregated.model_dump(mode="json")


def _coerce_agent_output(output: Any) -> AgentOutput:
    if isinstance(output, AgentOutput):
        return output
    if isinstance(output, Mapping):
        return AgentOutput.model_validate(output)
    return AgentOutput(agent_id="unknown_agent", status="error", summary="Invalid agent output")


def _case_summary(agent_outputs: dict[str, AgentOutput]) -> str:
    summaries = [output.summary for output in agent_outputs.values() if output.summary]
    if not summaries:
        return "에이전트 실행 결과가 없습니다."
    return " / ".join(summaries[:3])


def _dedupe_list(values: Any) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _dedupe_evidence_sources(values: Any) -> list[Any]:
    deduped: list[Any] = []
    seen: set[str] = set()
    for value in values:
        source_id = str(value.source_id)
        if source_id in seen:
            continue
        seen.add(source_id)
        deduped.append(value)
    return deduped
