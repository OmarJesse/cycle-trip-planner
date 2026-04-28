from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from src.agent.providers.base import LLMProvider, LLMResponse, StopReason


@dataclass
class MockResponse:
    content: list[dict[str, Any]]
    stop_reason: StopReason = StopReason.END_TURN


class MockProvider(LLMProvider):
    def __init__(
        self,
        *,
        responses: Iterable[MockResponse] | None = None,
        default_text: str = "OK (mock).",
        on_call: Callable[[list[dict[str, Any]]], None] | None = None,
    ):
        self._scripted = list(responses) if responses else []
        self._default_text = default_text
        self._index = 0
        self._on_call = on_call

    def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        if self._on_call is not None:
            self._on_call(messages)

        if self._index < len(self._scripted):
            scripted = self._scripted[self._index]
            self._index += 1
            return LLMResponse(stop_reason=scripted.stop_reason, content=scripted.content, model="mock")

        return LLMResponse(
            stop_reason=StopReason.END_TURN,
            content=[{"type": "text", "text": self._default_text}],
            model="mock",
        )


def text_block(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def tool_use_block(tool_id: str, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}
