from __future__ import annotations

from typing import Any, Dict, Optional

from app.clients.rag_client import RAGClient
from app.tools.base import ToolHandler


class RagToolHandler(ToolHandler):
    def __init__(self, rag_client: RAGClient) -> None:
        self.rag_client = rag_client

    async def handle(self, message: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.rag_client.ask(question=message, meta=meta or {})