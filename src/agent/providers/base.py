from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResponse:
    stop_reason: str | None
    content: list[Any]
    model: str | None = None


class LLMProvider(Protocol):
    def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse: ...

