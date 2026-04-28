from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class LLMProviderName(str, Enum):
    anthropic = "anthropic"
    gemini = "gemini"
    mock = "mock"


class CoreSettings(BaseModel):
    api_title: str = "Cycling Trip Planner Agent"

    llm_provider: LLMProviderName = Field(default=LLMProviderName.anthropic, alias="LLM_PROVIDER")
    llm_model: str = Field(default="claude-sonnet-4-6", alias="LLM_MODEL")

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    max_tool_rounds: int = Field(default=12, ge=1, le=30, alias="MAX_TOOL_ROUNDS")
    max_tokens: int = Field(default=2048, ge=64, le=8192, alias="MAX_TOKENS")

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"], alias="CORS_ALLOW_ORIGINS")
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"], alias="CORS_ALLOW_HEADERS")

    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=60, ge=1, le=100000, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600, alias="RATE_LIMIT_WINDOW_SECONDS")
