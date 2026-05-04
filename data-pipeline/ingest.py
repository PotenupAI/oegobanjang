from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent_runtime.rag.chunking import build_chunks, load_policy_documents, write_chunks_jsonl
from app.agent_runtime.rag.vector_store import write_chroma_jsonl


SEED_PATH = ROOT_DIR / "data-pipeline" / "seed" / "sample_policy_docs.jsonl"
CHUNKS_PATH = ROOT_DIR / "data-pipeline" / "processed" / "chunks" / "policy_chunks.jsonl"
CHROMA_JSONL_PATH = ROOT_DIR / "data-pipeline" / "processed" / "chunks" / "chroma_records.jsonl"


def run_ingest(
    *,
    seed_path: Path = SEED_PATH,
    chunks_path: Path = CHUNKS_PATH,
    chroma_jsonl_path: Path = CHROMA_JSONL_PATH,
) -> dict[str, object]:
    documents = load_policy_documents(seed_path)
    chunks = build_chunks(documents)
    write_chunks_jsonl(chunks, chunks_path)
    write_chroma_jsonl(chunks, chroma_jsonl_path)
    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "chunks_path": str(chunks_path),
        "chroma_jsonl_path": str(chroma_jsonl_path),
    }


if __name__ == "__main__":
    result = run_ingest()
    print(result)
