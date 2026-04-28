from __future__ import annotations

from typing import Any

from src.agent.providers.base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """
    Deterministic provider for tests: always returns a plain text response.
    """

    def __init__(self, reply: str = "OK (mock)."):
        self._reply = reply

    def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        return LLMResponse(
            stop_reason="end_turn",
            content=[{"type": "text", "text": self._reply}],
            model="mock",
        )

