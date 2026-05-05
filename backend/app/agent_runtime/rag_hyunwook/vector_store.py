<<<<<<< HEAD
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
=======
import os
from functools import lru_cache
from langchain_chroma import Chroma

from .embeddings import get_embedding_model

CHROMA_PERSIST_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "..", ".chroma", "foreign_hiring"
    )
)
CHROMA_COLLECTION_NAME = "foreign_hiring"


@lru_cache(maxsize=1)
def get_chroma_store() -> Chroma:
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=get_embedding_model(),
        persist_directory=CHROMA_PERSIST_DIR,
    )
>>>>>>> ccaa904 (Phase 3a 완료: LangChain 1.0 Agent Runtime 기본 골격 구현)
