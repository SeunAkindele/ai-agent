from __future__ import annotations

from typing import List, Protocol

from app.domain.models.rag_models import RAGSource


class QueryParser(Protocol):
    async def parse(self, question: str) -> str:
        ...


class EmbeddingProvider(Protocol):
    async def embed_query(self, text: str) -> List[float]:
        ...

    async def embed_document(self, text: str) -> List[float]:
        ...


class Retriever(Protocol):
    async def retrieve(self, query: str) -> tuple[str, list[RAGSource]]:
        ...


class AnswerGenerator(Protocol):
    async def generate(self, query: str, context: str) -> str:
        ...