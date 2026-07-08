from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Iterable, Protocol


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9가-힣_]+")


class EmbeddingClient(Protocol):
    dimensions: int

    def embed_text(self, text: str) -> list[float]:
        pass


@dataclass(frozen=True)
class LocalHashEmbeddingClient:
    dimensions: int = 64

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return normalize(vector)


def build_embedding_client(provider: str, dimensions: int) -> EmbeddingClient:
    if provider != "local_hash":
        raise ValueError(f"Unsupported embedding provider: {provider}")
    return LocalHashEmbeddingClient(dimensions=dimensions)


def tokenize(text: str) -> Iterable[str]:
    return (token.lower() for token in TOKEN_PATTERN.findall(text))


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 8) for value in vector]


def vector_to_pg_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"
