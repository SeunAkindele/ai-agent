from __future__ import annotations

from typing import Any, Dict

from app.application.services.rag_service import RAGService
from app.mcp.server import mcp


def register_rag_tools(rag_service: RAGService) -> None:
    @mcp.tool(name="ask")
    async def ask(question: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        result = await rag_service.ask(question)
        return {
            "answer": result.answer,
            "sources": [src.model_dump() for src in result.sources],
            "latency_ms": result.latency_ms,
        }