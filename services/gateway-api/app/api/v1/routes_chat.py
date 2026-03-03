import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.tool_router import choose_tool

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentAskRequest(BaseModel):
    message: str = Field(..., min_length=1)
    has_media: bool = False
    meta: Optional[Dict[str, Any]] = None


class AgentAskResponse(BaseModel):
    tool_used: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: Optional[int] = None
    trace_id: str
    router_reason: Optional[str] = None
    router_confidence: Optional[float] = None


@router.post("/agent/ask", response_model=AgentAskResponse)
async def agent_ask(payload: AgentAskRequest, request: Request):
    trace_id = uuid.uuid4().hex
    decision = choose_tool(payload.message, has_media=payload.has_media)

    logger.info(
        "tool selected",
        extra={
            "trace_id": trace_id,
        },
    )

    try:
        handler = request.app.state.tool_registry.get(decision.tool_name)
        result = await handler.handle(payload.message, payload.meta)
        return AgentAskResponse(
            tool_used=decision.tool_name,
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            latency_ms=result.get("latency_ms"),
            trace_id=trace_id,
            router_reason=decision.reason,
            router_confidence=decision.confidence,
        )
    except KeyError:
        return AgentAskResponse(
            tool_used="none",
            answer="No tool selected. Please ask a question or provide more context.",
            sources=[],
            latency_ms=None,
            trace_id=trace_id,
            router_reason=decision.reason,
            router_confidence=decision.confidence,
        )
    except Exception as e:
        logger.exception("tool execution failed")
        raise HTTPException(status_code=502, detail=f"Tool execution failed: {str(e)}")