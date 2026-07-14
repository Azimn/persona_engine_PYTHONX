"""Optional semantic-vector adapter with deterministic dependency-free providers."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, Sequence


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]: ...
    def embed_many(self, texts: Sequence[str]) -> list[list[float]]: ...
    def similarity(self, a: Sequence[float], b: Sequence[float]) -> float: ...
    def available(self) -> bool: ...
    def metadata(self) -> dict[str, str | int]: ...


class NoEmbeddingProvider:
    """Fail-closed provider used by the deterministic baseline."""

    def embed_text(self, text: str) -> list[float]:
        return []

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [[] for _ in texts]

    def similarity(self, a: Sequence[float], b: Sequence[float]) -> float:
        return 0.0

    def available(self) -> bool:
        return False

    def metadata(self) -> dict[str, str | int]:
        return {"provider": "none", "version": "1", "dimensions": 0}


class HashEmbeddingProvider:
    """Small stable token-hash vectors for optional local semantic scoring.

    This is not a neural embedding model. It proves the adapter, cache, and
    graceful fallback contracts without adding a runtime dependency.
    """

    def __init__(self, dimensions: int = 64):
        self.dimensions = max(8, min(512, int(dimensions)))
        self._cache: dict[str, list[float]] = {}

    def embed_text(self, text: str) -> list[float]:
        key = str(text or "")
        if key in self._cache:
            return list(self._cache[key])
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-z0-9']+", key.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = -1.0 if digest[4] & 1 else 1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        normalized = [value / norm for value in vector] if norm else vector
        self._cache[key] = normalized
        return list(normalized)

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def similarity(self, a: Sequence[float], b: Sequence[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return max(-1.0, min(1.0, sum(float(x) * float(y) for x, y in zip(a, b))))

    def available(self) -> bool:
        return True

    def metadata(self) -> dict[str, str | int]:
        return {"provider": "stable_hash", "version": "1", "dimensions": self.dimensions}
