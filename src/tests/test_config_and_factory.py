import os

import pytest

from src.agent.providers.factory import build_provider
from src.config.settings import LLMProviderName, Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MODEL", "mock-model")
    s = Settings()
    assert s.llm_provider == LLMProviderName.mock
    assert s.llm_model == "mock-model"


def test_factory_builds_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    s = Settings()
    p = build_provider(s)
    assert p.create_message(system="", messages=[], tools=[], max_tokens=100).model == "mock"


def test_factory_missing_anthropic_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    # Settings also reads from `.env`, so explicitly blank the key.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    s = Settings()
    with pytest.raises(ValueError):
        build_provider(s)

