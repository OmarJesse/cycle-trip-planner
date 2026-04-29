from __future__ import annotations

from fastapi.testclient import TestClient

from src.agent.providers.base import LLMProvider, LLMResponse, StopReason
from src.agent.providers.mock_provider import MockProvider, MockResponse, text_block, tool_use_block
from src.agent.runtime import Runtime
from src.api.app import app
from src.api.deps import get_runtime
from src.config.settings import Settings
from src.state.memory import InMemoryConversationStore
from src.tools.builtins import build_registry
from src.agent.v0 import MockOrchestratorV0
from src.agent.v1 import AgentOrchestrator


def _runtime_with(provider: LLMProvider) -> Runtime:
    settings = Settings()
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


def test_v1_chat_drives_multi_step_tool_use_over_http():
    scripted = [
        MockResponse(
            content=[
                text_block("Pulling the corridor."),
                tool_use_block("u1", "get_route", {"origin": "Amsterdam", "destination": "Copenhagen"}),
            ],
            stop_reason=StopReason.TOOL_USE,
        ),
        MockResponse(
            content=[
                tool_use_block("u2", "get_weather", {"location": "Copenhagen", "month": "June"}),
                tool_use_block("u3", "find_accommodation", {"near": "Copenhagen", "kind": "camping"}),
            ],
            stop_reason=StopReason.TOOL_USE,
        ),
        MockResponse(
            content=[text_block("## Trip summary\nDone.")],
            stop_reason=StopReason.END_TURN,
        ),
    ]
    rt = _runtime_with(MockProvider(responses=scripted))
    app.dependency_overrides[get_runtime] = lambda: rt

    try:
        client = TestClient(app)
        resp = client.post("/api/v1/chat", json={"message": "Plan Amsterdam to Copenhagen in June"})
        assert resp.status_code == 200
        data = resp.json()

        assert data["conversation_id"]
        assert data["reply"].startswith("## Trip summary")
        assert data["rounds"] == 3
        assert data["truncated"] is False
        assert data["error"] is None

        names = [c["name"] for c in data["tool_calls"]]
        assert names == ["get_route", "get_weather", "find_accommodation"]
        assert all(c["is_error"] is False for c in data["tool_calls"])
    finally:
        app.dependency_overrides.pop(get_runtime, None)


def test_v1_chat_returns_502_on_upstream_provider_failure():
    class _BoomProvider(LLMProvider):
        def create_message(self, **kwargs) -> LLMResponse:
            raise RuntimeError("upstream blew up")

    rt = _runtime_with(_BoomProvider())
    app.dependency_overrides[get_runtime] = lambda: rt

    try:
        client = TestClient(app)
        resp = client.post("/api/v1/chat", json={"message": "anything"})
        assert resp.status_code == 502
        data = resp.json()
        assert data["error"] is not None
        assert "upstream blew up" in data["error"]
        assert data["tool_calls"] == []
    finally:
        app.dependency_overrides.pop(get_runtime, None)


def test_v1_chat_returns_200_on_max_tokens_truncation():
    scripted = [
        MockResponse(
            content=[text_block("partial...")],
            stop_reason=StopReason.MAX_TOKENS,
        ),
    ]
    rt = _runtime_with(MockProvider(responses=scripted))
    app.dependency_overrides[get_runtime] = lambda: rt

    try:
        client = TestClient(app)
        resp = client.post("/api/v1/chat", json={"message": "anything"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["truncated"] is True
        assert data["error"] == "max_tokens"
    finally:
        app.dependency_overrides.pop(get_runtime, None)
