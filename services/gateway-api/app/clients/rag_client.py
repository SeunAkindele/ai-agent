from __future__ import annotations

from typing import Any, Dict, Optional

from app.clients.mcp_service_client import MCPServiceClient


class RAGClient:
    def __init__(
        self,
        endpoint_url: str,
        auth_token: Optional[str] = None,
        origin: str = "http://gateway-api.internal",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._mcp = MCPServiceClient(
            endpoint_url=endpoint_url,
            auth_token=auth_token,
            origin=origin,
            timeout_seconds=timeout_seconds,
        )

    async def start(self) -> None:
        await self._mcp.start()

    async def stop(self) -> None:
        await self._mcp.stop()

    async def ask(self, question: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "question": question,
            "meta": meta or {},
        }
        data = await self._mcp.call_tool("ask", payload)
        return {
            "answer": data.get("answer", "") or "",
            "sources": data.get("sources", []) or [],
            "latency_ms": data.get("latency_ms"),
        }

    async def list_tools(self) -> list[str]:
        return await self._mcp.list_tools()