from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from src.agent.providers.anthropic_provider import AnthropicProvider
from src.agent.runtime import Runtime
from src.agent.v0 import MockOrchestratorV0
from src.agent.v1 import AgentOrchestrator
from src.api.app import app
from src.api.deps import get_runtime
from src.config.settings import Settings
from src.state.memory import InMemoryConversationStore
from src.tools.builtins import build_registry


_LIVE_ENABLED = os.environ.get("RUN_LIVE_LLM") == "1"
_HAS_API_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))


pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not _LIVE_ENABLED, reason="set RUN_LIVE_LLM=1 to run live LLM smoke tests"),
    pytest.mark.skipif(not _HAS_API_KEY, reason="ANTHROPIC_API_KEY not set"),
]


def _live_runtime() -> Runtime:
    settings = Settings()
    api_key = os.environ["ANTHROPIC_API_KEY"]
    provider = AnthropicProvider(api_key=api_key, model=settings.llm_model)
    registry = build_registry()
    store = InMemoryConversationStore.create(
        max_age_seconds=settings.conversation_max_age_seconds,
        max_count=settings.conversation_max_count,
    )
    return Runtime(
        settings=settings,
        store=store,
        orchestrator_v0=MockOrchestratorV0(registry=registry),
        orchestrator_v1=AgentOrchestrator(settings=settings, provider=provider, registry=registry),
    )


def test_live_full_plan_returns_structured_markdown_and_calls_get_route():
    rt = _live_runtime()
    app.dependency_overrides[get_runtime] = lambda: rt
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/v1/chat",
            json={
                "message": "Plan a cycling trip from Amsterdam to Bremen.",
                "preferences": {
                    "origin": "Amsterdam",
                    "destination": "Bremen",
                    "daily_km": 100,
                    "month": "June",
                    "lodging_preference": "camping",
                    "nationality": "Canadian",
                    "stay_days": 5,
                },
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["error"] is None, f"agent returned an error: {data['error']}"
        assert data["truncated"] is False, "plan was truncated; bump MAX_TOKENS or shorten the trip"
        assert data["rounds"] >= 1

        names = [c["name"] for c in data["tool_calls"]]
        assert "get_route" in names, f"expected get_route in tool_calls, got: {names}"
        assert all(c["is_error"] is False for c in data["tool_calls"]), "a tool returned is_error=True"

        reply = data["reply"]
        assert "## Trip summary" in reply, "system prompt mandates a Trip summary heading"
        assert "## Day-by-day" in reply, "system prompt mandates a Day-by-day heading"
    finally:
        app.dependency_overrides.pop(get_runtime, None)


def test_live_preference_change_produces_adapted_plan_with_what_changed_line():
    rt = _live_runtime()
    app.dependency_overrides[get_runtime] = lambda: rt
    try:
        client = TestClient(app)

        first = client.post(
            "/api/v1/chat",
            json={
                "message": "Plan a cycling trip from Amsterdam to Bremen.",
                "preferences": {
                    "origin": "Amsterdam",
                    "destination": "Bremen",
                    "daily_km": 100,
                    "month": "June",
                    "lodging_preference": "camping",
                    "nationality": "Canadian",
                    "stay_days": 4,
                },
            },
        )
        assert first.status_code == 200, first.text
        first_data = first.json()
        assert first_data["error"] is None
        assert first_data["truncated"] is False
        cid = first_data["conversation_id"]
        first_reply = first_data["reply"]

        second = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": cid,
                "message": "Actually, slow it down to 60 km/day.",
                "preferences": {"daily_km": 60},
            },
        )
        assert second.status_code == 200, second.text
        data = second.json()
        assert data["error"] is None
        assert data["truncated"] is False

        adapted = data["reply"]
        assert "## Trip summary" in adapted
        assert "**What changed**" in adapted, (
            "system prompt requires a **What changed** line on preference adaptation; "
            "the model didn't follow the contract"
        )
        assert adapted != first_reply, "expected the adapted plan to differ from the original"
    finally:
        app.dependency_overrides.pop(get_runtime, None)
