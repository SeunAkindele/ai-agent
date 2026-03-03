from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_http_compat import router as http_router
from app.application.services.rag_service import PgVectorRetriever, RAGService
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
from app.mcp.server import mcp
from app.mcp.tools.rag_tool import register_rag_tools
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)

    db = PostgresManager(settings.postgres_dsn)
    await db.connect()
    pool = db.get_pool()

    vector_store = PgVectorStore(pool=pool, vector_dimension=settings.pgvector_dimension)

    parser = SimpleQueryParser()
    embedding_provider = HashEmbeddingProvider(dimension=settings.pgvector_dimension)
    retriever = PgVectorRetriever(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        top_k=settings.retrieval_top_k,
        tenant_id=None,  # later inject from auth/meta
        max_context_chars=settings.max_context_chars,
    )
    generator = StubAnswerGenerator()

    pipeline = RAGPipeline(
        parser=parser,
        retriever=retriever,
        generator=generator,
    )
    rag_service = RAGService(pipeline=pipeline)

    app.state.db = db
    app.state.db_ready = True
    app.state.rag_service = rag_service

    register_rag_tools(rag_service)

    try:
        yield
    finally:
        app.state.db_ready = False
        await db.disconnect()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_mcp_security_middleware(app, settings)

app.include_router(health_router)
app.include_router(http_router)

mcp_app = mcp.http_app(path="/")
app.mount("/mcp", mcp_app)