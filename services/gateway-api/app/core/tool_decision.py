from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDecision:
    tool_name: str
    confidence: float
    reason: str