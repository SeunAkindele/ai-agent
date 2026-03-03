from __future__ import annotations

from typing import Dict

from app.tools.base import ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        self._handlers[name] = handler

    def get(self, name: str) -> ToolHandler:
        if name not in self._handlers:
            raise KeyError(f"Unknown tool: {name}")
        return self._handlers[name]

    def names(self) -> list[str]:
        return sorted(self._handlers.keys())