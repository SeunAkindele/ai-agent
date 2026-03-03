from __future__ import annotations

from typing import Optional

from app.domain.interfaces import EmbeddingProvider, Retriever
from app.domain.models.rag_models import RAGResult
from app.infrastructure.db.vector_store import PgVectorStore
from app.rag.pipeline import RAGPipeline


class PgVectorRetriever(Retriever):
    def __init__(
        self,
        vector_store: PgVectorStore,
        embedding_provider: EmbeddingProvider,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        max_context_chars: int = 6000,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.top_k = top_k
        self.tenant_id = tenant_id
        self.max_context_chars = max_context_chars

    async def retrieve(self, query: str) -> tuple[str, list]:
        query_embedding = await self.embedding_provider.embed_query(query)
        sources = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=self.top_k,
            tenant_id=self.tenant_id,
        )

        parts: list[str] = []
        used = 0

        for src in sources:
            block = f"[{src.title or src.document_id}] {src.snippet.strip()}"
            if not block.strip():
                continue

            next_len = len(block) + 2
            if used + next_len > self.max_context_chars:
                break

            parts.append(block)
            used += next_len

        context = "\n\n".join(parts)
        return context, sources


class RAGService:
    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    async def ask(self, question: str) -> RAGResult:
        return await self.pipeline.run(question)