from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderName(str, Enum):
    anthropic = "anthropic"
    gemini = "gemini"
    mock = "mock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API
    api_title: str = "Cycling Trip Planner Agent"
    api_version: str = "1.0.0"

    # LLM selection
    llm_provider: LLMProviderName = Field(default=LLMProviderName.anthropic, alias="LLM_PROVIDER")
    llm_model: str = Field(default="claude-3-haiku-20240307", alias="LLM_MODEL")

    # Provider keys
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    # Runtime knobs
    max_tool_rounds: int = Field(default=6, ge=1, le=20, alias="MAX_TOOL_ROUNDS")
    max_tokens: int = Field(default=900, ge=64, le=4096, alias="MAX_TOKENS")

    # Feature flags
    include_structured_plan: bool = Field(default=True, alias="INCLUDE_STRUCTURED_PLAN")
    enable_optional_tools: bool = Field(default=True, alias="ENABLE_OPTIONAL_TOOLS")

    # CORS
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"], alias="CORS_ALLOW_ORIGINS")

