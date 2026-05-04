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
