from __future__ import annotations

from src.agent.providers.anthropic_provider import AnthropicProvider
from src.agent.providers.base import LLMProvider
from src.agent.providers.mock_provider import MockProvider
from src.config.settings import LLMProviderName, Settings


def build_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == LLMProviderName.mock:
        return MockProvider()

    if settings.llm_provider == LLMProviderName.anthropic:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is missing.")
        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)

    if settings.llm_provider == LLMProviderName.gemini:
        raise NotImplementedError(
            "Gemini provider not wired yet. Add GEMINI_API_KEY and implement provider in src/agent/providers/gemini_provider.py"
        )

    raise ValueError(f"Unknown provider: {settings.llm_provider}")

