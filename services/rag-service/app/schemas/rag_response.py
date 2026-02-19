from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    latency_ms: Optional[int] = None
