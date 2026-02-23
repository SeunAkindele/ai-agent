# services/rag-service/app/main.py
from __future__ import annotations

import inspect
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.mcp.server import mcp
from app.mcp.tools import rag as rag_tools

# ---------- MCP ASGI app ----------
# FastMCP docs: when mounting at /mcp, use path="/"
mcp_app = mcp.http_app(path="/")

app = FastAPI(
    title="rag-service",
    lifespan=mcp_app.lifespan,  # important
)

# Mount MCP endpoint at /mcp
app.mount("/mcp", mcp_app)

# ---------- Security (MCP streamable HTTP) ----------
# MCP spec says:
# - validate Origin
# - bind locally when possible
# - use authentication
# We'll enforce origin + bearer token for /mcp requests.
ALLOWED_MCP_ORIGINS = {
    x.strip()
    for x in os.getenv("ALLOWED_MCP_ORIGINS", "http://gateway-api.internal").split(",")
    if x.strip()
}
INTERNAL_MCP_TOKEN = os.getenv("INTERNAL_MCP_TOKEN", "dev-internal-token")


@app.middleware("http")
async def mcp_security_middleware(request: Request, call_next):
    path = request.url.path

    # Protect only the mounted MCP endpoint
    if path.startswith("/mcp"):
        # 1) Origin validation (MCP spec security guidance)
        origin = request.headers.get("origin")
        if not origin or origin not in ALLOWED_MCP_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid Origin"},
            )

        # 2) Simple bearer auth (recommended)
        auth = request.headers.get("authorization", "")
        expected = f"Bearer {INTERNAL_MCP_TOKEN}"
        if auth != expected:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
            )

    return await call_next(request)


# ---------- Optional normal HTTP routes ----------
@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "service": "rag-service"}


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


@app.post("/ask")
async def ask(payload: AskRequest) -> Dict[str, Any]:
    """
    Optional compatibility endpoint.
    Lets you test the same logic without MCP.
    """
    result = rag_tools.ask(payload.question)
    if inspect.isawaitable(result):
        result = await result

    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="Invalid RAG tool response")

    return {
        "answer": result.get("answer", "") or "",
        "sources": result.get("sources", []) or [],
        "latency_ms": result.get("latency_ms"),
    }