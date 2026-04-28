from __future__ import annotations

from dataclasses import dataclass

from src.agent.planning import build_day_by_day_plan, format_plan_markdown
from src.api.models import ConversationState, TripPreferences
from src.tools.registry import ToolRegistry


@dataclass
class MockOrchestratorV0:
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

        try:
            plan = build_day_by_day_plan(updated.preferences)
            updated.last_plan = plan
            reply = format_plan_markdown(plan, preferences=updated.preferences)
        except Exception:
            reply = (
                "Tell me:\n"
                "- start city and end city\n"
                "- daily km target\n"
                "- travel month\n"
                "- lodging preference and cadence\n"
                "- nationality + stay days (optional)"
            )

        updated.messages.append({"role": "assistant", "content": reply})
        return reply, updated

