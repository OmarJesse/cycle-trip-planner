from __future__ import annotations

from typing import Any, Optional

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.providers.base import LLMProvider
from src.tools.builtins import build_registry
from src.tools.registry import ToolError, ToolRegistry


def _extract_text_from_content(content: list[Any]) -> str:
    parts: list[str] = []
    for block in content:
        # SDK returns rich blocks with `.type` attr; but keep dict fallback
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


def run_claude_with_tools(
    *,
    messages: list[dict[str, Any]],
    max_rounds: int = 6,
    registry: ToolRegistry | None = None,
    provider: LLMProvider | None = None,
    max_tokens: int = 900,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Executes a bounded Claude tool-use loop.

    Returns: (assistant_text_reply, appended_messages)
    """
    registry = registry or build_registry()
    if provider is None:
        raise ValueError("provider is required")

    tools = [t.schema_for_llm() for t in registry.list()]
    history = list(messages)

    for _ in range(max_rounds):
        try:
            msg = provider.create_message(system=SYSTEM_PROMPT, messages=history, tools=tools, max_tokens=max_tokens)
        except Exception as e:
            # Surface common provider issues (e.g. invalid model name / auth) as a user-facing message.
            return f"LLM API error: {e}", history

        # assistant message content can include tool_use blocks
        assistant_content = msg.content
        history.append({"role": "assistant", "content": assistant_content})

        if getattr(msg, "stop_reason", None) != "tool_use":
            text = _extract_text_from_content(assistant_content)
            return (text or "OK."), history

        tool_use = _find_tool_use_block(assistant_content)
        if tool_use is None:
            return "I tried to call a tool but couldn’t parse the tool request.", history

        tool_name = getattr(tool_use, "name", None) or tool_use.get("name")
        tool_input = getattr(tool_use, "input", None) or tool_use.get("input") or {}
        tool_use_id = getattr(tool_use, "id", None) or tool_use.get("id")

        try:
            tool_output = registry.dispatch(tool_name, tool_input)
            tool_text = tool_output.model_dump_json()
        except ToolError as e:
            tool_text = f'{{"error": "{str(e)}"}}'

        history.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": [{"type": "text", "text": tool_text}],
                    }
                ],
            }
        )

    return "I hit the tool-call limit while planning. Try rephrasing or simplifying your request.", history

