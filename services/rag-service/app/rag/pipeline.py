from __future__ import annotations

import time

from app.domain.interfaces import AnswerGenerator, QueryParser, Retriever
from app.domain.models.rag_models import RAGResult


class RAGPipeline:
    def __init__(
        self,
        parser: QueryParser,
        retriever: Retriever,
        generator: AnswerGenerator,
    ) -> None:
        self.parser = parser
        self.retriever = retriever
        self.generator = generator

    async def run(self, question: str) -> RAGResult:
        start = time.time()

        parsed_query = await self.parser.parse(question)
        context, sources = await self.retriever.retrieve(parsed_query)
        answer = await self.generator.generate(parsed_query, context)

        return RAGResult(
            answer=answer,
            sources=sources,
            latency_ms=int((time.time() - start) * 1000),
        )