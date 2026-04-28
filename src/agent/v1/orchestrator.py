from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agent.orchestration import OrchestrationResult, run_agent_loop
from src.agent.prompts import system_prompt_blocks
from src.agent.providers.base import LLMProvider
from src.api.models import ConversationState, TripPreferences
from src.config.settings import Settings
from src.tools.registry import ToolRegistry


@dataclass
class AgentOrchestrator:
    settings: Settings
    provider: LLMProvider
    registry: ToolRegistry

    def handle_turn(
        self,
        *,
        state: ConversationState,
        user_message: str,
        preferences_override: TripPreferences | None = None,
    ) -> tuple[OrchestrationResult, ConversationState]:
        updated = state.model_copy(deep=True)

        if preferences_override:
            updated.preferences = updated.preferences.model_copy(
                update=preferences_override.model_dump(exclude_none=True)
            )

        framed_message = _frame_user_message(user_message, updated.preferences)
        updated.messages.append({"role": "user", "content": framed_message})

        cache = self.settings.prompt_cache_enabled
        result = run_agent_loop(
            system=system_prompt_blocks(cache=cache),
            tools=self.registry.schemas_for_llm(cache_breakpoint=cache),
            messages=_history_for_provider(updated.messages),
            registry=self.registry,
            provider=self.provider,
            max_rounds=self.settings.max_tool_rounds,
            max_tokens=self.settings.max_tokens,
        )

        updated.messages = _history_to_state(result.history)
        return result, updated


def _frame_user_message(user_message: str, prefs: TripPreferences) -> str:
    fields = prefs.model_dump(exclude_none=True)
    if not fields:
        return user_message
    rendered = "\n".join(f"  - {k}: {v}" for k, v in fields.items())
    return (
        f"{user_message}\n\n"
        f"[Active preferences — these are authoritative; do not re-ask for any field listed here:\n"
        f"{rendered}\n]"
    )


def _history_for_provider(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def _history_to_state(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": m["role"], "content": m["content"]} for m in history]
