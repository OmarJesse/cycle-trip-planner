from __future__ import annotations

from typing import Any

from anthropic import Anthropic, NotFoundError
from anthropic._exceptions import AnthropicError

from src.agent.providers.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, *, api_key: str, model: str):
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._fallback_models = self._dedupe_preserve_order(
            [
                model,
                "claude-sonnet-4-6",
                "claude-opus-4-7",
                "claude-haiku-3-5",
                "claude-3-5-sonnet-latest",
                "claude-3-5-sonnet-20240620",
                "claude-3-haiku-20240307",
                "claude-3-sonnet-20240229",
                "claude-3-opus-20240229",
            ]
        )

    @property
    def model(self) -> str:
        return self._model

    @staticmethod
    def _dedupe_preserve_order(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    def _list_available_models(self) -> list[str]:
        """
        Return model IDs available to this API key.

        The python SDK has had multiple representations over time, so this
        intentionally tolerates different shapes.
        """
        try:
            models = self._client.models.list()
        except Exception:
            return []

        ids: list[str] = []
        data = getattr(models, "data", None)
        if isinstance(data, list):
            for item in data:
                model_id = getattr(item, "id", None)
                if isinstance(model_id, str) and model_id:
                    ids.append(model_id)
                elif isinstance(item, dict):
                    mid = item.get("id")
                    if isinstance(mid, str) and mid:
                        ids.append(mid)

        return ids

    def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        last_err: Exception | None = None

        tried: list[str] = []
        for m in self._fallback_models:
            tried.append(m)
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

        # If the configured/fallback models aren't available on this key,
        # discover what *is* available and retry.
        available = [m for m in self._list_available_models() if m not in tried]
        for m in available:
            tried.append(m)
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
            except AnthropicError as e:
                last_err = e
                break

        if last_err:
            raise last_err
        raise RuntimeError("AnthropicProvider failed to create message.")

