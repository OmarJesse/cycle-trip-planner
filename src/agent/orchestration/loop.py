from __future__ import annotations

from typing import Any

from src.agent.orchestration.blocks import (
    block_attr,
    extract_text,
    extract_tool_uses,
    normalize_assistant_content,
)
from src.agent.orchestration.types import OrchestrationResult, ToolInvocation
from src.agent.providers.base import LLMProvider, StopReason
from src.exception import provider_failure_result
from src.tools.registry import ToolError, ToolRegistry


def run_agent_loop(
    *,
    system: str | list[dict[str, Any]],
    tools: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    registry: ToolRegistry,
    provider: LLMProvider,
    max_rounds: int,
    max_tokens: int,
) -> OrchestrationResult:
    history: list[dict[str, Any]] = list(messages)
    tool_calls: list[ToolInvocation] = []

    for round_idx in range(1, max_rounds + 1):
        try:
            msg = provider.create_message(
                system=system,
                messages=history,
                tools=tools,
                max_tokens=max_tokens,
            )
        except Exception as e:
            return provider_failure_result(
                e,
                history=history,
                tool_calls=tool_calls,
                rounds=round_idx - 1,
            )

        history.append({"role": "assistant", "content": normalize_assistant_content(msg.content)})

        if msg.stop_reason == StopReason.MAX_TOKENS:
            text = extract_text(msg.content)
            return OrchestrationResult(
                reply=text or "I ran out of response tokens before finishing the plan. Increase MAX_TOKENS or split the request.",
                history=history,
                tool_calls=tool_calls,
                rounds=round_idx,
                truncated=True,
                error=StopReason.MAX_TOKENS.value,
            )

        if msg.stop_reason != StopReason.TOOL_USE:
            return OrchestrationResult(
                reply=extract_text(msg.content) or "",
                history=history,
                tool_calls=tool_calls,
                rounds=round_idx,
            )

        tool_uses = extract_tool_uses(msg.content)
        if not tool_uses:
            return OrchestrationResult(
                reply=extract_text(msg.content) or "I tried to call a tool but couldn't parse the request.",
                history=history,
                tool_calls=tool_calls,
                rounds=round_idx,
            )

        invocations, results_payload = _dispatch_tool_uses(tool_uses, registry)
        tool_calls.extend(invocations)
        history.append({"role": "user", "content": results_payload})

    return OrchestrationResult(
        reply="I hit the tool-call round limit before finishing the plan. Try simplifying or splitting the request.",
        history=history,
        tool_calls=tool_calls,
        rounds=max_rounds,
        truncated=True,
    )


def _dispatch_tool_uses(
    tool_uses: list[Any],
    registry: ToolRegistry,
) -> tuple[list[ToolInvocation], list[dict[str, Any]]]:
    invocations: list[ToolInvocation] = []
    payload: list[dict[str, Any]] = []

    for tu in tool_uses:
        name = block_attr(tu, "name") or ""
        tool_input = block_attr(tu, "input") or {}
        tool_use_id = block_attr(tu, "id")

        try:
            output = registry.dispatch(name, tool_input)
            output_dict = output.model_dump()
            tool_text = output.model_dump_json()
            is_error = False
        except ToolError as e:
            output_dict = None
            tool_text = f'{{"error": {e!r}}}'
            is_error = True

        invocations.append(
            ToolInvocation(
                name=name,
                input=dict(tool_input) if isinstance(tool_input, dict) else {},
                output=output_dict,
                is_error=is_error,
            )
        )
        payload.append(
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "is_error": is_error,
                "content": [{"type": "text", "text": tool_text}],
            }
        )

    return invocations, payload
