from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import Settings


def register_mcp_security_middleware(app: FastAPI, settings: Settings) -> None:
    @app.middleware("http")
    async def mcp_security_middleware(request: Request, call_next):
        path = request.url.path

        if path.startswith("/mcp") and path != "/mcp/health":
            origin = request.headers.get("origin")
            if not origin or origin not in settings.allowed_mcp_origins:
                return JSONResponse(status_code=403, content={"detail": "Invalid Origin"})

            auth = request.headers.get("authorization", "")
            expected = f"Bearer {settings.internal_mcp_token}"
            if auth != expected:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        return await call_next(request)