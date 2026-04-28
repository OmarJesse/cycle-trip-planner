from typing import Any

from src.agent.prompts.loader import load_system_prompt


SYSTEM_PROMPT = load_system_prompt()


def system_prompt_blocks(*, cache: bool = False) -> list[dict[str, Any]]:
    block: dict[str, Any] = {"type": "text", "text": SYSTEM_PROMPT}
    if cache:
        block["cache_control"] = {"type": "ephemeral"}
    return [block]


__all__ = ["SYSTEM_PROMPT", "system_prompt_blocks"]
