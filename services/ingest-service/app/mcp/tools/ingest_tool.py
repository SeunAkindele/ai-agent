from __future__ import annotations

from typing import Any, Dict, Optional

from app.application.services.rag_service import RAGService
from app.mcp.server import mcp

_rag_service: Optional[RAGService] = None


def set_rag_service(service: RAGService) -> None:
    global _rag_service
    _rag_service = service


@mcp.tool(name="ask")
async def ask(question: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if _rag_service is None:
        raise RuntimeError("RAG service not initialized yet")
    result = await _rag_service.ask(question)
    return {
        "answer": result.answer,
        "sources": [src.model_dump() for src in result.sources],
        "latency_ms": result.latency_ms,
    }