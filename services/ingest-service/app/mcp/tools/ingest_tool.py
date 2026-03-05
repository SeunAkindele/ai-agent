from __future__ import annotations

from typing import Any, Dict, Optional

from app.application.services.ingest_service import IngestService
from app.mcp.server import mcp

_ingest_service: Optional[IngestService] = None


def set_ingest_service(service: IngestService) -> None:
    global _ingest_service
    _ingest_service = service


@mcp.tool(name="ingest")
async def ingest(source: str, data_type: str) -> Dict[str, Any]:
    if _ingest_service is None:
        raise RuntimeError("Ingest service not initialized yet")
    await _ingest_service.ingest(source, data_type)
    return {"message": "Ingested successfully"}