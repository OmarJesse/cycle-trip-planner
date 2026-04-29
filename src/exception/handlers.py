from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.agent.orchestration.types import OrchestrationResult, ToolInvocation
from src.exception.errors import AgentError, LLMProviderError
from src.logger.logging import get_logger
from src.tools.registry import ToolError


logger = get_logger("cycling_trip_planner.agent")
api_logger = get_logger("cycling_trip_planner.api")


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
        upstream_failure=True,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ToolError)
    async def _tool_error_handler(_: Request, exc: ToolError) -> JSONResponse:
        api_logger.warning("ToolError: %s", exc)
        return JSONResponse(
            status_code=400,
            content={"error": str(exc), "type": "tool_error"},
        )

    @app.exception_handler(LLMProviderError)
    async def _llm_provider_error_handler(_: Request, exc: LLMProviderError) -> JSONResponse:
        api_logger.exception("LLMProviderError: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"error": str(exc), "type": "llm_provider_error"},
        )

    @app.exception_handler(AgentError)
    async def _agent_error_handler(_: Request, exc: AgentError) -> JSONResponse:
        api_logger.exception("AgentError: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "type": "agent_error"},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        api_logger.info("RequestValidationError: %s", exc.errors())
        return JSONResponse(
            status_code=422,
            content={"error": "Invalid request payload.", "type": "validation_error", "details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        api_logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error.", "type": "internal_error"},
        )
