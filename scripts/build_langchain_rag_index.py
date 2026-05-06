#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent_runtime.langchain_runtime.vectorstore import build_persistent_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build LangChain-compatible RAG index artifacts.")
    parser.add_argument(
        "--chunks",
        default="data-pipeline/processed/chunks/all_chunks.jsonl",
        help="Input chunk JSONL path.",
    )
    parser.add_argument(
        "--output",
        default="data-pipeline/processed/chroma_langchain",
        help="Output directory for persistent index artifacts.",
    )
    args = parser.parse_args()

    manifest = build_persistent_index(chunk_path=Path(args.chunks), output_dir=Path(args.output))
    print(
        f"Wrote {manifest['index_type']} index: "
        f"{manifest['document_count']} documents -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
