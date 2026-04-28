from __future__ import annotations

from typing import Any, Optional

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.providers.base import LLMProvider
from src.tools.builtins import build_registry
from src.tools.registry import ToolError, ToolRegistry


def _extract_text_from_content(content: list[Any]) -> str:
    parts: list[str] = []
    for block in content:
        btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
        if btype == "text":
            txt = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else "")
            parts.append(txt)
    return "\n".join([p for p in parts if p]).strip()


def _find_tool_use_block(content: list[Any]) -> Optional[Any]:
    for block in content:
        btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
        if btype == "tool_use":
            return block
    return None


def _find_tool_use_blocks(content: list[Any]) -> list[Any]:
    out: list[Any] = []
    for block in content:
        btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
        if btype == "tool_use":
            out.append(block)
    return out


def run_claude_with_tools(
    *,
    messages: list[dict[str, Any]],
    max_rounds: int = 6,
    registry: ToolRegistry | None = None,
    provider: LLMProvider | None = None,
    max_tokens: int = 900,
) -> tuple[str, list[dict[str, Any]]]:
    registry = registry or build_registry()
    if provider is None:
        raise ValueError("provider is required")

    tools = [t.schema_for_llm() for t in registry.list()]
    history = list(messages)

    for _ in range(max_rounds):
        try:
            msg = provider.create_message(system=SYSTEM_PROMPT, messages=history, tools=tools, max_tokens=max_tokens)
        except Exception as e:
            return f"LLM API error: {e}", history

        assistant_content = msg.content
        history.append({"role": "assistant", "content": assistant_content})

        if getattr(msg, "stop_reason", None) != "tool_use":
            text = _extract_text_from_content(assistant_content)
            return (text or "OK."), history

        tool_use = _find_tool_use_block(assistant_content)
        if tool_use is None:
            return "I tried to call a tool but couldn’t parse the tool request.", history

        # Claude can return multiple tool_use blocks in a single assistant message.
        # Anthropic requires a tool_result for *each* tool_use in the *next* message.
        tool_uses = _find_tool_use_blocks(assistant_content)
        if not tool_uses:
            tool_uses = [tool_use]

        tool_results: list[dict[str, Any]] = []
        for tu in tool_uses:
            tool_name = getattr(tu, "name", None) or tu.get("name")
            tool_input = getattr(tu, "input", None) or tu.get("input") or {}
            tool_use_id = getattr(tu, "id", None) or tu.get("id")

            try:
                tool_output = registry.dispatch(tool_name, tool_input)
                tool_text = tool_output.model_dump_json()
                is_error = False
            except ToolError as e:
                tool_text = f'{{"error": "{str(e)}"}}'
                is_error = True

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "is_error": is_error,
                    "content": [{"type": "text", "text": tool_text}],
                }
            )

        history.append({"role": "user", "content": tool_results})

    return "I hit the tool-call limit while planning. Try rephrasing or simplifying your request.", history

