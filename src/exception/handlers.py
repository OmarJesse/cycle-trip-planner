from __future__ import annotations

from typing import Any

from src.agent.orchestration.types import OrchestrationResult, ToolInvocation
from src.exception.errors import LLMProviderError
from src.logger.logging import get_logger


logger = get_logger("cycling_trip_planner.agent")


def provider_failure_result(
    exc: Exception,
    *,
    history: list[dict[str, Any]],
    tool_calls: list[ToolInvocation],
    rounds: int,
) -> OrchestrationResult:
    error = exc if isinstance(exc, LLMProviderError) else LLMProviderError(str(exc), original=exc)
    logger.exception("LLM provider call failed: %s", error)
    return OrchestrationResult(
        reply=f"LLM API error: {error}",
        history=history,
        tool_calls=tool_calls,
        rounds=rounds,
        error=str(error),
    )
