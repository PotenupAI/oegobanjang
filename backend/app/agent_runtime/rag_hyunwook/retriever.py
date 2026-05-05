<<<<<<< HEAD
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .citation import can_use_as_answer_evidence, format_citation


TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def load_chunks(path: str | Path) -> list[dict[str, Any]]:
    chunk_path = Path(path)
    chunks: list[dict[str, Any]] = []

    with chunk_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid chunk JSONL at {chunk_path}:{line_no}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Invalid chunk JSONL at {chunk_path}:{line_no}: row must be an object")
            chunks.append(record)

    return chunks


class PolicyRetriever:
    def __init__(self, chunks: list[dict[str, Any]]) -> None:
        self.chunks = chunks
=======
from dataclasses import dataclass, field
from langchain_core.documents import Document

from .vector_store import get_chroma_store
from .citation import build_citations
from app.agent_runtime.schemas.tool import Citation

CONFIDENCE_THRESHOLD = 0.5


@dataclass
class RetrievalResult:
    documents: list[Document] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    found: bool = True
    reason: str = ""


class RAGRetriever:
    def __init__(self):
        self._store = None

    @property
    def store(self):
        if self._store is None:
            self._store = get_chroma_store()
        return self._store
>>>>>>> ccaa904 (Phase 3a 완료: LangChain 1.0 Agent Runtime 기본 골격 구현)

    def search(
        self,
        query: str,
<<<<<<< HEAD
        *,
        top_k: int = 3,
        filters: dict[str, str] | None = None,
        answer_evidence_only: bool = True,
    ) -> list[dict[str, Any]]:
        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        for chunk in self.chunks:
            metadata = chunk.get("metadata", {})
            if filters and not _matches_filters(metadata, filters):
                continue
            if answer_evidence_only and not can_use_as_answer_evidence(metadata):
                continue

            haystack = " ".join(
                [
                    str(chunk.get("title", "")),
                    str(metadata.get("title", "")),
                    str(metadata.get("publisher", "")),
                    str(metadata.get("source_id", "")),
                    str(chunk.get("text", "")),
                    str(metadata.get("doc_type", "")),
                    str(metadata.get("source_type", "")),
                ]
            )
            tokens = tokenize(haystack)
            if not tokens:
                continue

            token_set = set(tokens)
            overlap = query_tokens & token_set
            if not overlap:
                continue

            score = len(overlap) / max(len(query_tokens), 1)
            score += min(tokens.count(token) for token in overlap) * 0.01
            title_tokens = set(tokenize(str(metadata.get("title", ""))))
            score += len(query_tokens & title_tokens) * 0.2
            result = {
                **chunk,
                "score": round(score, 6),
                "citation": format_citation(chunk),
            }
            scored.append((score, result))

        scored.sort(key=lambda item: (-item[0], str(item[1].get("chunk_id", ""))))
        return [result for _, result in scored[:top_k]]


def _matches_filters(metadata: dict[str, Any], filters: dict[str, str]) -> bool:
    for key, expected in filters.items():
        actual = metadata.get(key)
        if isinstance(actual, list):
            if expected not in actual and "ALL" not in actual:
                return False
        elif actual != expected:
            return False
    return True


def retrieve_policy_documents(
    query: str,
    chunk_path: str | Path,
    *,
    top_k: int = 3,
    filters: dict[str, str] | None = None,
    answer_evidence_only: bool = True,
) -> list[dict[str, Any]]:
    return PolicyRetriever(load_chunks(chunk_path)).search(
        query,
        top_k=top_k,
        filters=filters,
        answer_evidence_only=answer_evidence_only,
    )
=======
        visa_type: str | None = None,
        evidence_grade: str | None = None,
        k: int = 5,
    ) -> RetrievalResult:
        where_filter: dict = {}
        if visa_type:
            where_filter["visa_type"] = visa_type
        if evidence_grade:
            where_filter["evidence_grade"] = evidence_grade

        try:
            if where_filter:
                results_with_scores = self.store.similarity_search_with_relevance_scores(
                    query, k=k, filter=where_filter
                )
            else:
                results_with_scores = self.store.similarity_search_with_relevance_scores(
                    query, k=k
                )
        except Exception:
            return RetrievalResult(found=False, reason="vector_store_error")

        if not results_with_scores:
            return RetrievalResult(found=False, reason="no_results")

        docs = [doc for doc, score in results_with_scores if score >= CONFIDENCE_THRESHOLD]
        if not docs:
            return RetrievalResult(found=False, reason="low_confidence")

        return RetrievalResult(
            documents=docs,
            citations=build_citations(docs),
            found=True,
        )
>>>>>>> ccaa904 (Phase 3a 완료: LangChain 1.0 Agent Runtime 기본 골격 구현)
