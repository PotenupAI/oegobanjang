from __future__ import annotations

from typing import Any, TypedDict


class EvidenceEvent(TypedDict, total=False):
    timestamp: str
    work_item_id: str
    agent_id: str
    event_type: str
    action_type: str
    input: dict[str, Any]
    output: dict[str, Any]
    confidence: float
    human_override: bool
    evidence_chunk_ids: list[str]


class EvidenceCitation(TypedDict):
    source_id: str
    chunk_id: str
    title: str
    publisher: str
    url: str
    evidence_grade: str


class EvidencePackageChunk(TypedDict):
    chunk_id: str
    source_id: str
    title: str
    text: str
    evidence_grade: str
    doc_type: str
    citation: EvidenceCitation


class MissingEvidence(TypedDict):
    reason: str
    query: str


class EvidencePolicy(TypedDict):
    answer_evidence_grades: list[str]
    excluded_grades: list[str]
    synthetic_official_claims_allowed: bool


class EvidencePackage(TypedDict):
    status: str
    request_id: str
    query: str
    case_type: str
    retrieved_chunks: list[EvidencePackageChunk]
    citations: list[EvidenceCitation]
    missing_evidence: list[MissingEvidence]
    evidence_policy: EvidencePolicy
