from __future__ import annotations

import hashlib
from typing import List


class SimpleQueryParser:
    async def parse(self, question: str) -> str:
        return question.strip()


class HashEmbeddingProvider:
    """
    Development-only deterministic embedding provider.
    Replace this with OpenAI / Azure OpenAI / Voyage / BGE / etc in production.
    """

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension

    async def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    async def embed_document(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: List[float] = []

        idx = 0
        while len(values) < self.dimension:
            b = seed[idx % len(seed)]
            values.append((b / 255.0) * 2 - 1)  # normalize to [-1, 1]
            idx += 1

        return values


class StubAnswerGenerator:
    """
    Replace with your real LLM later.
    """

    async def generate(self, query: str, context: str) -> str:
        context = (context or "").strip()
        if not context:
            return "I could not find any relevant context for your question yet."

        return (
            "Based on the retrieved context, here is the best available answer:\n\n"
            f"{context[:2200]}"
        )