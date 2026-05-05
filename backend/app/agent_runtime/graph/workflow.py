from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from app.agent_runtime.guardrails import check_output, enforce_guardrails
from app.agent_runtime.graph.nodes.approval_gate import evaluate_approval
from app.agent_runtime.graph.nodes.evidence_logger import append_event
from app.agent_runtime.graph.nodes.executor import execute_plan
from app.agent_runtime.graph.nodes.final_response import build_final_response
from app.agent_runtime.graph.nodes.intent_router import route_intent
from app.agent_runtime.graph.nodes.planner import create_plan
from app.agent_runtime.middleware.pii_filter import mask_payload


DEFAULT_CHUNK_PATH = Path("data-pipeline/processed/chunks/all_chunks.jsonl")


def run_workflow(payload: dict[str, Any] | None) -> dict[str, Any]:
    incoming = deepcopy(payload or {})
    work_item_id = str(incoming.get("request_id") or incoming.get("work_item_id") or "work_item")
    runtime_mode = str(incoming.get("runtime_mode") or "deterministic")
    logged_incoming = mask_payload(incoming)
    input_state = mask_payload(incoming.get("input_state") or {})

    routed = route_intent(incoming)
    case_type = routed["case_type"]
    current_state = routed["current_state"]
    next_state = routed["next_state"]
    detected_intents = routed["detected_intents"]
    guardrail_violations = _dedupe(
        list(routed.get("guardrail_violations", [])) + check_output({"input_state": input_state})
    )

    evidence_events: list[dict[str, Any]] = []
    append_event(
        evidence_events,
        work_item_id=work_item_id,
        agent_id="intent_router",
        action_type="route",
        event_type="intent_classified",
        input_data=logged_incoming,
        output_data={"detected_intents": detected_intents, **routed},
    )

    plan_context = {
        "case_type": case_type,
        "detected_intents": detected_intents,
        "input_state": input_state,
        "current_state": current_state,
        "request_id": incoming.get("request_id"),
        "guardrail_violations": guardrail_violations,
    }
    plan = create_plan(plan_context)
    append_event(
        evidence_events,
        work_item_id=work_item_id,
        agent_id="planner",
        action_type="plan",
        event_type="plan_created",
        input_data=plan_context,
        output_data=plan,
    )

    execution = execute_plan(
        {
            "plan": plan,
            "input_state": input_state,
            "case_type": case_type,
            "current_state": current_state,
            "retrieved_evidence": incoming.get("retrieved_evidence") or {},
        }
    )
    append_event(
        evidence_events,
        work_item_id=work_item_id,
        agent_id="executor",
        action_type="execute_tool",
        event_type="tool_executed",
        input_data={"plan": plan, "input_state": input_state},
        output_data=execution,
    )

    append_event(
        evidence_events,
        work_item_id=work_item_id,
        agent_id="approval_gate",
        action_type="approve",
        event_type="approval_requested",
        input_data={"execution": execution, **logged_incoming},
        output_data={"approval_required": True},
    )

    approval = evaluate_approval(
        {
            **incoming,
            "execution": execution,
            "approval_required": True,
        }
    )
    append_event(
        evidence_events,
        work_item_id=work_item_id,
        agent_id="approval_gate",
        action_type="approve",
        event_type="approval_completed",
        input_data={"human_approved": incoming.get("human_approved", False)},
        output_data=approval,
        human_override=bool(incoming.get("human_approved")),
    )

    status = "in_progress"
    if approval["status"] == "APPROVED":
        current_state = "handoff_package"
        next_state = "completed"
        status = "completed"
    elif execution.get("blocked_reason"):
        status = "blocked"

    judgment = None
    judgment_report = None
    if runtime_mode == "langchain_judgment" and status != "blocked" and not execution.get("guardrail_violations"):
        from app.agent_runtime.llm.client import ProviderError, build_judgment_client, ensure_json_only
        from app.agent_runtime.llm.judgment_chain import run_judgment_chain
        from app.agent_runtime.rag.evidence_package import build_evidence_package
        from app.agent_runtime.reporting.report import build_basic_report

        evidence_package = build_evidence_package(
            request_id=work_item_id,
            query=str(incoming.get("user_message") or ""),
            case_type=case_type,
            chunk_path=DEFAULT_CHUNK_PATH,
            top_k=3,
            answer_evidence_only=True,
        )
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
            evidence_chunk_ids=[chunk["chunk_id"] for chunk in evidence_package["retrieved_chunks"]],
        )
        try:
            client = build_judgment_client(
                fallback_response_text=_default_judgment_json(
                    request_id=work_item_id,
                    case_type=case_type,
                    detected_intents=detected_intents,
                    evidence_package=evidence_package,
                )
            )
            raw_judgment = ensure_json_only(
                client.generate_json(
                    [
                        {
                            "role": "user",
                            "content": str(incoming.get("user_message") or ""),
                        }
                    ]
                )
            )
            judgment = run_judgment_chain(
                user_message=str(incoming.get("user_message") or ""),
                detected_intents=detected_intents,
                evidence_package=evidence_package,
                client=_StaticJudgmentClient(raw_judgment),
            )
        except (ProviderError, ValueError) as exc:
            append_event(
                evidence_events,
                work_item_id=work_item_id,
                agent_id="judgment_node",
                action_type="block",
                event_type="block",
                input_data={"runtime_mode": runtime_mode},
                output_data={"reason": str(exc)},
            )
            status = "blocked"
            judgment_error = {
                "status": "blocked",
                "reason": "llm_provider_error",
                "message": str(exc),
            }
            return {
                "request_id": incoming.get("request_id"),
                "user_id": incoming.get("user_id"),
                "company_id": incoming.get("company_id"),
                "case_type": case_type,
                "current_state": current_state,
                "next_state": next_state,
                "detected_intents": detected_intents,
                "runtime_mode": runtime_mode,
                "input_state": input_state,
                "plan": plan,
                "execution": execution,
                "approval": approval,
                "approval_required": approval["required"],
                "final_response": {
                    "status": "blocked",
                    "approval_required": approval["required"],
                    "message": "LLM 판단 생성 중 오류가 발생했습니다.",
                    "error": judgment_error,
                },
                "evidence_events": evidence_events,
                "status": "blocked",
                "reason": "llm_provider_error",
            }
        judgment_report = build_basic_report(judgment)
        append_event(
            evidence_events,
            work_item_id=work_item_id,
            agent_id="judgment_node",
            action_type="llm_judgment_generated",
            event_type="llm_judgment_generated",
            input_data={"runtime_mode": runtime_mode, "detected_intents": detected_intents},
            output_data=judgment.model_dump(mode="json"),
        )
        append_event(
            evidence_events,
            work_item_id=work_item_id,
            agent_id="judgment_node",
            action_type="risk_flagged",
            event_type="risk_flagged",
            input_data={"judgment_status": judgment.status},
            output_data={"risk_flags": judgment_report["risk_flags"]},
        )

    final_response = build_final_response(
        {
            "case_type": case_type,
            "current_state": current_state,
            "next_state": next_state,
            "approval": approval,
            "execution": execution,
            "judgment_report": judgment_report,
        }
    )
    append_event(
        evidence_events,
        work_item_id=work_item_id,
        agent_id="final_response",
        action_type="final_response_generated",
        event_type="final_response_generated",
        input_data={"current_state": current_state, "next_state": next_state},
        output_data=final_response,
    )

    result: dict[str, Any] = {
        "request_id": incoming.get("request_id"),
        "user_id": incoming.get("user_id"),
        "company_id": incoming.get("company_id"),
        "case_type": case_type,
        "current_state": current_state,
        "next_state": next_state,
        "detected_intents": detected_intents,
        "runtime_mode": runtime_mode,
        "input_state": input_state,
        "plan": plan,
        "execution": execution,
        "approval": approval,
        "approval_required": approval["required"],
        "final_response": final_response,
        "evidence_events": evidence_events,
        "status": status,
    }
    if judgment is not None:
        result["judgment"] = judgment.model_dump(mode="json")
        result["judgment_report"] = judgment_report

    if execution.get("guardrail_violations"):
        append_event(
            evidence_events,
            work_item_id=work_item_id,
            agent_id="guardrails",
            action_type="block",
            event_type="block",
            input_data={"detected_intents": detected_intents},
            output_data={"violations": execution.get("guardrail_violations", [])},
        )
        result["status"] = "blocked"
        result["reason"] = execution.get("blocked_reason") or "blocked_by_guardrails"
        result["guardrail_violations"] = list(execution.get("guardrail_violations", []))
        return result

    guarded = enforce_guardrails(result)
    if guarded.get("status") == "blocked":
        append_event(
            evidence_events,
            work_item_id=work_item_id,
            agent_id="guardrails",
            action_type="block",
            event_type="block",
            input_data=result,
            output_data={"violations": guarded.get("violations", [])},
        )
        result["status"] = "blocked"
        result["reason"] = guarded.get("reason", "blocked_by_guardrails")
        result["guardrail_violations"] = list(guarded.get("violations", []))
        return result

    return result


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


class _StaticJudgmentClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text

    def generate_json(self, messages: list[dict[str, str]]) -> str:
        return self.response_text


def _default_judgment_json(
    *,
    request_id: str,
    case_type: str,
    detected_intents: list[str],
    evidence_package: dict[str, Any],
) -> str:
    import json

    evidence_summary = [
        {
            "claim": str(chunk["text"])[:120],
            "source_id": str(chunk["source_id"]),
            "evidence_grade": str(chunk["evidence_grade"]).upper(),
        }
        for chunk in evidence_package.get("retrieved_chunks", [])
    ] or [
        {
            "claim": "공식 근거가 충분하지 않아 담당자 검토가 필요합니다.",
            "source_id": "insufficient_evidence",
            "evidence_grade": "E",
        }
    ]
    evidence_source_ids = [item["source_id"] for item in evidence_summary]

    return json.dumps(
        {
            "status": "draft",
            "request_id": request_id,
            "case_type": case_type,
            "detected_intents": detected_intents,
            "summary": "요청을 근거 기반 판단 리포트 초안으로 정리했습니다.",
            "evidence_summary": evidence_summary,
            "risk_flags": [
                {
                    "type": "approval_required_action",
                    "level": "medium",
                    "reason": "외부 발송, 전달, 완료 처리는 담당자 승인 이후에만 가능합니다.",
                    "source_ids": evidence_source_ids,
                }
            ],
            "readiness_status": "needs_review",
            "missing_inputs": [],
            "follow_up_questions": [],
            "approval_required": True,
            "blocked": False,
            "guardrail_notes": [],
            "prohibited_actions": [],
            "next_actions": ["담당자가 판단 리포트와 승인 대기 작업을 검토합니다."],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
