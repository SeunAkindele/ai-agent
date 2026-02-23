import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import FORCE_TOOL
from app.core.tool_router import choose_tool, ToolName
from app.clients.rag_client import RAGClient

router = APIRouter()
rag_client = RAGClient()


# ----------------------------
# Request / Response
# ----------------------------

class AgentAskRequest(BaseModel):
    message: str = Field(..., min_length=1)

    # If your upload route attaches files, you can set this true
    # (for now client can send it)
    has_media: bool = False

    meta: Optional[Dict[str, Any]] = None


class AgentAskResponse(BaseModel):
    tool_used: str
    answer: str

    # rag fields (only meaningful if tool_used == "rag")
    sources: List[Dict[str, Any]] = []
    latency_ms: Optional[int] = None

    # helpful for debugging/observability
    trace_id: str


# ----------------------------
# Single public API
# ----------------------------

@router.post("/agent/ask", response_model=AgentAskResponse)
async def agent_ask(payload: AgentAskRequest):
    trace_id = uuid.uuid4().hex

    # Decide which tool to use
    tool: ToolName
    if FORCE_TOOL:
        tool = FORCE_TOOL  # type: ignore
    else:
        tool = choose_tool(payload.message, has_media=payload.has_media)

    # ---- RAG (fully implemented)
    if tool == "rag":
        try:
            rag_result = await rag_client.ask(payload.message)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"RAG service failed: {str(e)}")

        return AgentAskResponse(
            tool_used="rag",
            answer=rag_result.get("answer", ""),
            sources=rag_result.get("sources", []),
            latency_ms=rag_result.get("latency_ms"),
            trace_id=trace_id,
        )

    # ---- Other tools (not implemented yet in gateway)
    # These placeholders keep your “one API + router” architecture consistent.
    if tool == "media":
        return AgentAskResponse(
            tool_used="media",
            answer="Media tool selected, but media integration is not implemented in the gateway yet.",
            sources=[],
            latency_ms=None,
            trace_id=trace_id,
        )

    if tool == "cards":
        return AgentAskResponse(
            tool_used="cards",
            answer="Cards tool selected, but cards integration is not implemented in the gateway yet.",
            sources=[],
            latency_ms=None,
            trace_id=trace_id,
        )

    if tool == "ingest":
        return AgentAskResponse(
            tool_used="ingest",
            answer="Ingest tool selected, but ingest integration is not implemented in the gateway yet.",
            sources=[],
            latency_ms=None,
            trace_id=trace_id,
        )

    # none or unknown
    return AgentAskResponse(
        tool_used="none",
        answer="No tool selected. Please ask a question or provide more context.",
        sources=[],
        latency_ms=None,
        trace_id=trace_id,
    )
