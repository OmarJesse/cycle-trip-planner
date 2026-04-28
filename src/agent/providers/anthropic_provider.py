from __future__ import annotations

from typing import Any

from anthropic import Anthropic, NotFoundError

from src.agent.providers.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, *, api_key: str, model: str):
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._fallback_models = [
            model,
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
        ]

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
        last_err: Exception | None = None
        for m in self._fallback_models:
            try:
                self._model = m
                msg = self._client.messages.create(
                    model=m,
                    system=system,
                    max_tokens=max_tokens,
                    messages=messages,
                    tools=tools,
                )
                return LLMResponse(stop_reason=getattr(msg, "stop_reason", None), content=msg.content, model=m)
            except NotFoundError as e:
                last_err = e
                continue

        if last_err:
            raise last_err
        raise RuntimeError("AnthropicProvider failed to create message.")

