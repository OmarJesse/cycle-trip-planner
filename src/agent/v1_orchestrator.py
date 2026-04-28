from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agent.orchestration_loop import run_claude_with_tools
from src.agent.providers.base import LLMProvider
from src.agent.planning import build_day_by_day_plan, format_plan_markdown
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
    ) -> tuple[str, ConversationState]:
        updated = state.model_copy(deep=True)
        if preferences_override:
            updated.preferences = updated.preferences.model_copy(update=preferences_override.model_dump(exclude_none=True))

        updated.messages.append({"role": "user", "content": user_message})

        claude_messages = [{"role": m["role"], "content": m["content"]} for m in updated.messages]
        reply, new_history = run_claude_with_tools(
            messages=claude_messages,
            max_rounds=self.settings.max_tool_rounds,
            registry=self.registry,
            provider=self.provider,
            max_tokens=self.settings.max_tokens,
        )

        updated.messages = []
        for m in new_history:
            if m.get("role") == "user" and isinstance(m.get("content"), str):
                updated.messages.append({"role": "user", "content": m["content"]})

        updated.messages.append({"role": "assistant", "content": reply})

        # If the LLM fails, fall back to a deterministic plan so the UI still works.
        if reply.startswith("LLM API error:"):
            try:
                plan = build_day_by_day_plan(updated.preferences)
                updated.last_plan = plan
                reply = reply + "\n\n" + format_plan_markdown(plan, preferences=updated.preferences)
                updated.messages[-1]["content"] = reply
            except Exception:
                pass
        else:
            # If we have enough preferences to plan, always attach a plan to the response.
            # This prevents the UX from stalling on "I'll check..." replies.
            p = updated.preferences
            has_minimum = bool(p.origin and p.destination and p.month and p.daily_km)
            if has_minimum and updated.last_plan is None:
                try:
                    plan = build_day_by_day_plan(p)
                    updated.last_plan = plan
                    reply = reply + "\n\n" + format_plan_markdown(plan, preferences=p)
                    updated.messages[-1]["content"] = reply
                except Exception:
                    pass

        return reply, updated

