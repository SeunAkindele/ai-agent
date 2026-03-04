from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ToolHandler(ABC):
    @abstractmethod
    async def handle(self, message: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError