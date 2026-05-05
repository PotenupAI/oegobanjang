from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agent_runtime.schemas.evidence import (
    EvidenceCitation,
    EvidencePackage,
    EvidencePackageChunk,
)

from .citation import ANSWER_EVIDENCE_GRADES as _ANSWER_EVIDENCE_GRADES
from .retriever import retrieve_policy_documents


ANSWER_EVIDENCE_GRADES = frozenset(sorted(_ANSWER_EVIDENCE_GRADES))
EXCLUDED_EVIDENCE_GRADES = frozenset({"C", "D", "F"})
REQUIRED_PACKAGE_METADATA = (
    "source_id",
    "title",
    "publisher",
    "url",
    "doc_type",
    "evidence_grade",
)


def build_evidence_package(
    *,
    request_id: str,
    query: str,
    case_type: str,
    chunk_path: str | Path,
    top_k: int = 3,
    filters: dict[str, str] | None = None,
    answer_evidence_only: bool = True,
) -> EvidencePackage:
    results = retrieve_policy_documents(
        query,
        chunk_path,
        top_k=top_k,
        filters=filters,
        answer_evidence_only=answer_evidence_only,
    )
    chunks = [_to_package_chunk(result, answer_evidence_only=answer_evidence_only) for result in results]
    citations = [chunk["citation"] for chunk in chunks]

    return {
        "status": "ready" if chunks else "insufficient_evidence",
        "request_id": request_id,
        "query": query,
        "case_type": case_type,
        "retrieved_chunks": chunks,
        "citations": citations,
        "missing_evidence": [] if chunks else [{"reason": "no_retrieval_results", "query": query}],
        "evidence_policy": {
            "answer_evidence_grades": sorted(ANSWER_EVIDENCE_GRADES),
            "excluded_grades": sorted(EXCLUDED_EVIDENCE_GRADES),
            "synthetic_official_claims_allowed": False,
        },
    }


def _to_package_chunk(
    result: dict[str, Any],
    *,
    answer_evidence_only: bool,
) -> EvidencePackageChunk:
    metadata = result.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Missing evidence package metadata: metadata")

    _validate_metadata(metadata)
    evidence_grade = str(metadata["evidence_grade"]).upper()
    if answer_evidence_only and evidence_grade not in ANSWER_EVIDENCE_GRADES:
        raise ValueError(f"Evidence grade is not allowed for answer evidence: {evidence_grade}")

    citation = _normalize_citation(result)

    return {
        "chunk_id": str(result["chunk_id"]),
        "source_id": str(result["source_id"]),
        "title": str(result.get("title") or metadata["title"]),
        "text": str(result["text"]),
        "evidence_grade": evidence_grade,
        "doc_type": str(metadata["doc_type"]),
        "citation": citation,
    }


def _validate_metadata(metadata: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_PACKAGE_METADATA if field not in metadata or metadata[field] is None]
    if missing:
        raise ValueError(f"Missing evidence package metadata: {', '.join(sorted(missing))}")


def _normalize_citation(result: dict[str, Any]) -> EvidenceCitation:
    citation = result.get("citation")
    if not isinstance(citation, dict):
        raise ValueError("Missing evidence package metadata: citation")

    required = ("source_id", "chunk_id", "title", "publisher", "url", "evidence_grade")
    missing = [field for field in required if citation.get(field) is None]
    if missing:
        raise ValueError(f"Missing evidence package metadata: citation.{', citation.'.join(sorted(missing))}")

    return {
        "source_id": str(citation["source_id"]),
        "chunk_id": str(citation["chunk_id"]),
        "title": str(citation["title"]),
        "publisher": str(citation["publisher"]),
        "url": str(citation["url"]),
        "evidence_grade": str(citation["evidence_grade"]).upper(),
    }
