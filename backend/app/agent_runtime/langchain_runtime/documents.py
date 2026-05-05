from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agent_runtime.langchain_runtime.schemas import PolicyDocument


PRESERVED_METADATA_FIELDS = {
    "source_id",
    "title",
    "publisher",
    "evidence_grade",
    "chunk_type",
    "doc_type",
    "source_type",
    "url",
    "mission_agent",
    "visa_type",
    "country",
    "industry",
}


def load_policy_documents(chunk_path: str | Path) -> list[PolicyDocument]:
    documents: list[PolicyDocument] = []
    with Path(chunk_path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if not isinstance(record, dict):
                raise ValueError(f"Invalid chunk row at line {line_no}")
            documents.append(chunk_to_document(record))
    return documents


def chunk_to_document(chunk: dict[str, Any]) -> PolicyDocument:
    metadata = dict(chunk.get("metadata") or {})
    metadata.setdefault("chunk_id", chunk.get("chunk_id"))
    metadata.setdefault("title", chunk.get("title") or metadata.get("title"))

    preserved = {
        key: metadata.get(key)
        for key in PRESERVED_METADATA_FIELDS
        if key in metadata and metadata.get(key) is not None
    }
    preserved["chunk_id"] = metadata.get("chunk_id")
    return PolicyDocument(page_content=str(chunk.get("text") or ""), metadata=preserved)
