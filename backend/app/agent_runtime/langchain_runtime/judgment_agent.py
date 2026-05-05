from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agent_runtime.langchain_runtime.schemas import LangChainJudgmentResult, RetrievedPolicyContext
from app.agent_runtime.langchain_runtime.tools import (
    DEFAULT_CHUNK_PATH,
    SAFE_TOOL_NAMES,
    assess_readiness,
    get_safe_tools,
    retrieve_policy_context,
)
from app.agent_runtime.llm.parser import parse_judgment_json


def run_fake_langchain_judgment(
    *,
    request_id: str,
    user_message: str,
    case_type: str,
    detected_intents: list[str],
    input_state: dict[str, Any] | None = None,
    chunk_path: str | Path = DEFAULT_CHUNK_PATH,
) -> LangChainJudgmentResult:
    safe_tools = get_safe_tools()
    if set(safe_tools) != SAFE_TOOL_NAMES:
        raise ValueError("unsafe tool registry")

    context = retrieve_policy_context(user_message, chunk_path=chunk_path, top_k=3)
    readiness = assess_readiness(
        {
            "company_id": (input_state or {}).get("company_id"),
            "current_state": (input_state or {}).get("current_state", "site_check"),
            "input_state": input_state or {},
        }
    )
    source_ids = [item["source_id"] for item in context if item["source_id"]]
    evidence_summary = [
        {
            "claim": item["snippet"][:120] or "정책 근거가 검색되었습니다.",
            "source_id": item["source_id"],
            "evidence_grade": item["evidence_grade"],
        }
        for item in context
    ]
    if not evidence_summary:
        evidence_summary = [
            {
                "claim": "공식 근거가 충분하지 않아 담당자 검토가 필요합니다.",
                "source_id": "insufficient_evidence",
                "evidence_grade": "E",
            }
        ]
        source_ids = ["insufficient_evidence"]

    report = parse_judgment_json(
        json.dumps(
            {
                "status": "draft",
                "request_id": request_id,
                "case_type": case_type,
                "detected_intents": detected_intents,
                "summary": "LangChain adapter fake runner가 safe tool 결과를 구조화했습니다.",
                "evidence_summary": evidence_summary,
                "risk_flags": [
                    {
                        "type": "approval_required_action",
                        "level": "medium",
                        "reason": "발송, 제출, 완료 처리는 담당자 승인 이후에만 가능합니다.",
                        "source_ids": source_ids,
                    }
                ],
                "readiness_status": _judgment_readiness(str(readiness["readiness_status"])),
                "missing_inputs": readiness["missing_inputs"],
                "follow_up_questions": readiness["follow_up_questions"],
                "approval_required": True,
                "blocked": False,
                "guardrail_notes": [],
                "prohibited_actions": [],
                "next_actions": ["담당자가 근거와 누락 입력을 검토합니다."],
            },
            ensure_ascii=False,
        )
    )
    return LangChainJudgmentResult(
        report=report,
        used_tools=["retrieve_policy_context", "assess_readiness"],
        retrieved_context=[RetrievedPolicyContext(**item) for item in context],
    )


def _judgment_readiness(readiness_status: str) -> str:
    return {
        "ready_for_review": "needs_review",
        "needs_human_review": "needs_review",
        "needs_more_information": "needs_review",
    }.get(readiness_status, "needs_review")
