from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunking import write_chunks_jsonl
from .embeddings import deterministic_embedding


def build_chroma_ready_records(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_ids: dict[str, int] = {}
    for chunk in chunks:
        base_id = str(chunk["chunk_id"])
        occurrence = seen_ids.get(base_id, 0)
        seen_ids[base_id] = occurrence + 1
        record_id = base_id if occurrence == 0 else f"{base_id}__dup_{occurrence:04d}"
        metadata = dict(chunk["metadata"])
        metadata.setdefault("original_chunk_id", base_id)
        records.append(
            {
                "id": record_id,
                "text": chunk["text"],
                "metadata": metadata,
                "embedding": deterministic_embedding(chunk["text"]),
            }
        )
    return records


def write_chroma_jsonl(chunks: list[dict[str, Any]], path: str | Path) -> Path:
    return write_chunks_jsonl(build_chroma_ready_records(chunks), path)


def build_persistent_chroma_collection(
    chunks: list[dict[str, Any]],
    *,
    persist_path: str | Path,
    collection_name: str = "workbridge_policy",
    reset: bool = False,
) -> Any:
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError("chromadb is required for persistent vector store indexing") from exc

    client = chromadb.PersistentClient(path=str(persist_path))
    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    collection = client.get_or_create_collection(name=collection_name)
    records = build_chroma_ready_records(chunks)
    if not records:
        return collection

    collection.upsert(
        ids=[record["id"] for record in records],
        documents=[record["text"] for record in records],
        embeddings=[record["embedding"] for record in records],
        metadatas=[_sanitize_metadata(record["metadata"], record["id"]) for record in records],
    )
    return collection


def query_chroma_collection(collection: Any, query: str, *, top_k: int = 3) -> list[dict[str, Any]]:
    result = collection.query(
        query_embeddings=[deterministic_embedding(query)],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    rows: list[dict[str, Any]] = []
    for index, chunk_id in enumerate(ids):
        metadata = dict(metadatas[index] or {})
        rows.append(
            {
                "chunk_id": chunk_id,
                "source_id": metadata.get("source_id"),
                "text": documents[index],
                "metadata": metadata,
                "distance": distances[index] if index < len(distances) else None,
            }
        )
    return rows


def _sanitize_metadata(metadata: dict[str, Any], chunk_id: str) -> dict[str, str | int | float | bool]:
    sanitized: dict[str, str | int | float | bool] = {"chunk_id": chunk_id}
    for key, value in metadata.items():
        if value is None:
            sanitized[key] = ""
        elif isinstance(value, str | int | float | bool):
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = ",".join(str(item) for item in value)
        else:
            sanitized[key] = str(value)
    sanitized["chunk_id"] = chunk_id
    return sanitized
