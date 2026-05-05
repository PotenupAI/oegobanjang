from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agent_runtime.rag.retriever import retrieve_policy_documents
from app.agent_runtime.tools.quota_tool import assess_readiness as quota_assess_readiness


DEFAULT_CHUNK_PATH = Path("data-pipeline/processed/chunks/all_chunks.jsonl")
SAFE_TOOL_NAMES = {"retrieve_policy_context", "assess_readiness"}
FORBIDDEN_TOOL_NAMES = {
    "send_worker_message",
    "government_portal_submit",
    "complete_case",
    "external_export",
    "destructive_db_update",
}


def retrieve_policy_context(
    query: str,
    *,
    chunk_path: str | Path = DEFAULT_CHUNK_PATH,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    results = retrieve_policy_documents(query, chunk_path, top_k=top_k, answer_evidence_only=True)
    return [
        {
            "source_id": str(result.get("metadata", {}).get("source_id") or result.get("source_id") or ""),
            "title": str(result.get("metadata", {}).get("title") or result.get("title") or ""),
            "snippet": str(result.get("text") or "")[:500],
            "evidence_grade": str(result.get("metadata", {}).get("evidence_grade") or "").upper(),
            "score": result.get("score"),
        }
        for result in results
    ]


def assess_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    return quota_assess_readiness(payload)


def get_safe_tools() -> dict[str, object]:
    return {
        "retrieve_policy_context": retrieve_policy_context,
        "assess_readiness": assess_readiness,
    }
