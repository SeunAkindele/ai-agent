from app.rag.container import run_rag

def ask(question: str) -> dict:
    """
    MCP tool: rag.ask
    """
    return run_rag(question)
