import inspect
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mcp.tools import rag as rag_tools

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


@router.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "service": "rag-service"}


@router.post("/ask")
async def ask(payload: AskRequest) -> Dict[str, Any]:
    """
    HTTP wrapper around the same rag logic used by MCP tools.
    """
    try:
        result = rag_tools.ask(payload.question)

        # Supports both async and sync tool functions
        if inspect.isawaitable(result):
            result = await result

        if not isinstance(result, dict):
            raise RuntimeError("rag_tools.ask must return a dict")

        return {
            "answer": result.get("answer", "") or "",
            "sources": result.get("sources", []) or [],
            "latency_ms": result.get("latency_ms", None),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG processing failed: {e}")