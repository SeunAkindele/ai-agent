from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes_chat import router as chat_router
from app.clients.rag_client import RAGClient
from app.core.config import settings
from app.core.logging import setup_logging
from app.tools.rag_handler import RagToolHandler
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)

    rag_client = RAGClient(
        endpoint_url=settings.rag_mcp_url,
        auth_token=settings.internal_mcp_token,
        origin=settings.internal_mcp_origin,
        timeout_seconds=settings.mcp_timeout_seconds,
    )
    await rag_client.start()

    registry = ToolRegistry()
    registry.register("rag", RagToolHandler(rag_client))

    app.state.rag_client = rag_client
    app.state.tool_registry = registry

    try:
        tools = await rag_client.list_tools()
        logger.info("gateway connected to rag MCP tools: %s", tools)
    except Exception as e:
        logger.warning("failed to list rag tools at startup: %s", str(e))

    try:
        yield
    finally:
        await rag_client.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(chat_router, prefix=settings.api_prefix)