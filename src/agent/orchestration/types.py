from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolInvocation:
    name: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    is_error: bool


@dataclass
class OrchestrationResult:
    reply: str
    history: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[ToolInvocation] = field(default_factory=list)
    rounds: int = 0
    truncated: bool = False
    error: str | None = None
    upstream_failure: bool = False
