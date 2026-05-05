<<<<<<< HEAD
from __future__ import annotations

import hashlib

import numpy as np


def deterministic_embedding(text: str, *, dimensions: int = 64) -> list[float]:
    """Local deterministic embedding for tests and offline MVP indexing."""
    vector = np.zeros(dimensions, dtype=float)
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % dimensions
        vector[index] += 1.0

    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector.tolist()
    return (vector / norm).tolist()
=======
from functools import lru_cache
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_model() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,
    )
>>>>>>> ccaa904 (Phase 3a 완료: LangChain 1.0 Agent Runtime 기본 골격 구현)
