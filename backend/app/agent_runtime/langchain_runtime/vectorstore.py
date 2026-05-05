from __future__ import annotations

import json
from pathlib import Path

from app.agent_runtime.langchain_runtime.documents import load_policy_documents


def build_persistent_index(
    *,
    chunk_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Build a local persistent index artifact without requiring network access."""

    documents = load_policy_documents(chunk_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    docs_path = target / "documents.jsonl"
    with docs_path.open("w", encoding="utf-8") as f:
        for document in documents:
            f.write(document.model_dump_json() + "\n")

    manifest = {
        "index_type": "langchain_chroma_compatible_fallback",
        "document_count": len(documents),
        "documents_path": str(docs_path),
        "metadata_fields": sorted({key for doc in documents for key in doc.metadata}),
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
