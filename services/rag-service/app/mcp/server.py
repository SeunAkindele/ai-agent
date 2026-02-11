from mcp.server.fastmcp import FastMCP
from app.rag.container import pipeline

mcp = FastMCP("rag-service")

@mcp.tool()
def ask(question: str) -> str:
    """Answer a question using RAG"""
    return pipeline.run(question)
