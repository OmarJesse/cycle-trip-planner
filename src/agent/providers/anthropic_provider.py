from __future__ import annotations

from typing import Any

from anthropic import Anthropic

from src.agent.providers.base import LLMProvider, LLMResponse, StopReason


class AnthropicProvider(LLMProvider):
    def __init__(self, *, api_key: str, model: str):
        self._client = Anthropic(api_key=api_key)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        msg = self._client.messages.create(
            model=self._model,
            system=system,
            max_tokens=max_tokens,
            messages=messages,
            tools=tools,
        )
        raw_stop_reason = getattr(msg, "stop_reason", None)
        return LLMResponse(
            stop_reason=StopReason(raw_stop_reason) if raw_stop_reason is not None else None,
            content=msg.content,
            model=self._model,
        )
