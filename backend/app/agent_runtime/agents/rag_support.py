from __future__ import annotations

from pathlib import Path

from app.agent_runtime.rag.retriever import retrieve_policy_documents
from app.agent_runtime.schemas.agent_output import EvidenceSourceRef


DEFAULT_CHUNK_PATH = Path("data-pipeline/processed/chunks/all_chunks.jsonl")


def evidence_refs_for_query(
    query: str,
    *,
    expected_source_ids: list[str],
    top_k: int = 5,
) -> list[EvidenceSourceRef]:
    refs: list[EvidenceSourceRef] = []
    try:
        chunks = retrieve_policy_documents(
            query,
            DEFAULT_CHUNK_PATH,
            top_k=top_k,
            answer_evidence_only=True,
        )
    except (FileNotFoundError, ValueError):
        chunks = []

    for chunk in chunks:
        source_id = str(chunk.get("source_id") or chunk.get("metadata", {}).get("source_id") or "")
        if source_id not in expected_source_ids:
            continue
        refs.append(
            EvidenceSourceRef(
                source_id=source_id,
                chunk_id=str(chunk.get("chunk_id") or "") or None,
                evidence_grade=str(chunk.get("evidence_grade") or chunk.get("metadata", {}).get("evidence_grade") or "")
                or None,
                title=str(chunk.get("title") or chunk.get("metadata", {}).get("title") or "") or None,
            )
        )

    seen = {ref.source_id for ref in refs}
    for source_id in expected_source_ids:
        if source_id not in seen:
            refs.append(EvidenceSourceRef(source_id=source_id))

    return refs
