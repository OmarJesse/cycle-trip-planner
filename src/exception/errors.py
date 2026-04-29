from __future__ import annotations


class AgentError(Exception):
    pass


class LLMProviderError(AgentError):
    def __init__(self, message: str, *, original: Exception | None = None):
        super().__init__(message)
        self.original = original


class MissingPreferencesError(AgentError):
    pass
