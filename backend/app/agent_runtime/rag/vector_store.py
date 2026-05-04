from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunking import write_chunks_jsonl
from .embeddings import deterministic_embedding


def build_chroma_ready_records(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for chunk in chunks:
        records.append(
            {
                "id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": deterministic_embedding(chunk["text"]),
            }
        )
    return records


def write_chroma_jsonl(chunks: list[dict[str, Any]], path: str | Path) -> Path:
    return write_chunks_jsonl(build_chroma_ready_records(chunks), path)
