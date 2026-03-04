from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.domain.models.rag_models import AskRequest

router = APIRouter()


@router.post("/ask")
async def ask(payload: AskRequest, request: Request):
    rag_service = request.app.state.rag_service
    result = await rag_service.ask(payload.question)

    if result is None:
        raise HTTPException(status_code=500, detail="Invalid RAG response")

    return {
        "answer": result.answer,
        "sources": [src.model_dump() for src in result.sources],
        "latency_ms": result.latency_ms,
    }