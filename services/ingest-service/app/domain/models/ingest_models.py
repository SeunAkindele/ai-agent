from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RAGSource(BaseModel):
    chunk_id: str
    document_id: str
    title: Optional[str] = None
    snippet: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGResult(BaseModel):
    answer: str
    sources: List[RAGSource] = Field(default_factory=list)
    latency_ms: int


class AskRequest(BaseModel):
    question: str
    meta: Dict[str, Any] = Field(default_factory=dict)