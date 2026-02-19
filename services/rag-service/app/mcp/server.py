from fastmcp.server.fastmcp import FastMCP
from app.mcp.tools import rag as rag_tools

mcp = FastMCP(
    name="rag-service",
    instructions="RAG question answering tool service"
)

# exposes rag.ask
mcp.tool()(rag_tools.ask)
