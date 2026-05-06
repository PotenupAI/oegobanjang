from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agent_runtime.langchain_runtime.documents import load_policy_documents
from app.agent_runtime.rag.vector_store import build_persistent_chroma_collection


def build_persistent_index(
    *,
    chunk_path: str | Path,
    output_dir: str | Path,
    collection_name: str = "workbridge_policy",
) -> dict[str, object]:
    """Build a local Chroma persistent index plus JSONL companion artifacts."""

    chunks = _load_chunks(chunk_path)
    documents = load_policy_documents(chunk_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    docs_path = target / "documents.jsonl"
    with docs_path.open("w", encoding="utf-8") as f:
        for document in documents:
            f.write(document.model_dump_json() + "\n")

    collection = build_persistent_chroma_collection(
        chunks,
        persist_path=target,
        collection_name=collection_name,
        reset=True,
    )

    manifest = {
        "index_type": "chroma_persistent",
        "collection_name": collection_name,
        "document_count": len(documents),
        "persist_path": str(target),
        "chroma_sqlite_path": str(target / "chroma.sqlite3"),
        "fallback_documents_path": str(docs_path),
        "documents_path": str(docs_path),
        "metadata_fields": sorted({key for doc in documents for key in doc.metadata}),
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**manifest, "collection": collection}


def _load_chunks(chunk_path: str | Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    with Path(chunk_path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if not isinstance(record, dict):
                raise ValueError(f"Invalid chunk row at line {line_no}")
            chunks.append(record)
    return chunks
