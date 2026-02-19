from typing import Any, Dict, Optional

# This import depends on the MCP python client you’re using.
# Common pattern is an async client that connects to the MCP server transport.
# Replace with your actual MCP client import.
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

class RAGClient:
    """
    Calls MCP tool: rag.ask
    The MCP server is your rag-service 'server.py' that exposes rag.ask.
    """

    def __init__(self, rag_mcp_cmd: Optional[list[str]] = None):
        # Command used to start/connect to the rag-service MCP server via stdio.
        # In docker you may connect differently (http transport, websocket, etc).
        self.rag_mcp_cmd = rag_mcp_cmd or ["python", "-m", "app.server"]

    async def ask(self, question: str) -> Dict[str, Any]:
        """
        Calls MCP tool rag.ask(question) and returns normalized output.
        """
        async with stdio_client(self.rag_mcp_cmd) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # IMPORTANT: tool name must match what your rag-service registers: rag.ask
                result = await session.call_tool("ask", {"question": question})
                # Some MCP clients return {"content": ...} or structured content
                data = result.get("content", result)

        return {
            "answer": data.get("answer", "") or "",
            "sources": data.get("sources", []) or [],
            "latency_ms": data.get("latency_ms", None),
        }
