from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import register_mcp_security_middleware
from app.infrastructure.db.postgres import PostgresManager
from app.infrastructure.db.vector_store import PgVectorStore
from app.infrastructure.llm.providers import (
    HashEmbeddingProvider,
    SimpleQueryParser,
    StubAnswerGenerator,
)
from app.application.services.rag_service import PgVectorRetriever, RAGService
from app.mcp.server import mcp
from app.mcp.tools.rag_tool import set_rag_service
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

setup_logging(settings.log_level)

# --- build dependencies once at import/startup ---
db = PostgresManager(settings.postgres_dsn)


@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({
        "ok": True,
        "service": "rag-service",
        "db_ready": getattr(mcp, "_db_ready", False),
    })


async def _init_services() -> None:
    await db.connect()
    pool = db.get_pool()

    vector_store = PgVectorStore(
        pool=pool,
        vector_dimension=settings.pgvector_dimension,
    )

    parser = SimpleQueryParser()
    embedding_provider = HashEmbeddingProvider(dimension=settings.pgvector_dimension)
    retriever = PgVectorRetriever(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        top_k=settings.retrieval_top_k,
        tenant_id=None,
        max_context_chars=settings.max_context_chars,
    )
    generator = StubAnswerGenerator()

    pipeline = RAGPipeline(
        parser=parser,
        retriever=retriever,
        generator=generator,
    )

    rag_service = RAGService(pipeline=pipeline)
    set_rag_service(rag_service)

    mcp._db_ready = True
    logger.info("rag-service startup complete")


async def _teardown_services() -> None:
    mcp._db_ready = False
    await db.disconnect()
    logger.info("rag-service shutdown complete")


# Wrap the FastMCP lifespan so our init/teardown actually runs.
# on_event("startup") is silently ignored when a lifespan is already set
# (which FastMCP does), so we chain ours around it instead.
_original_app = mcp.http_app(path="/mcp")
_mcp_lifespan = _original_app.router.lifespan_context


@asynccontextmanager
async def _combined_lifespan(app):
    async with _mcp_lifespan(app):
        await _init_services()
        try:
            yield
        finally:
            await _teardown_services()


_original_app.router.lifespan_context = _combined_lifespan
app = _original_app

register_mcp_security_middleware(app, settings)