from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    source: str
    data_type: str
    meta: Dict[str, Any] = Field(default_factory=dict)