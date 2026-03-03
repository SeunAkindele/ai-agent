from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    db_ok = getattr(request.app.state, "db_ready", False)
    return {
        "ok": True,
        "service": "rag-service",
        "db_ready": db_ok,
    }