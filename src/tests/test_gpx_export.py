from __future__ import annotations

from fastapi.testclient import TestClient

from src.agent.providers.base import StopReason
from src.agent.providers.mock_provider import MockProvider, MockResponse, text_block, tool_use_block
from src.agent.runtime import Runtime
from src.agent.v0 import MockOrchestratorV0
from src.agent.v1 import AgentOrchestrator
from src.api.app import app
from src.api.deps import get_runtime
from src.api.gpx import GPX_MEDIA_TYPE, route_to_gpx
from src.api.v1.gpx import extract_latest_route
from src.config.settings import Settings
from src.state.memory import InMemoryConversationStore
from src.tools.builtins import build_registry
from src.tools.get_route import GetRouteOutput, RoutePoint


def _runtime(provider) -> Runtime:
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


def test_route_to_gpx_emits_well_formed_gpx_with_waypoints():
    route = GetRouteOutput(
        origin="Amsterdam",
        destination="Copenhagen",
        total_distance_km=620.5,
        suggested_days=6,
        waypoints=[
            RoutePoint(name="Amsterdam", lat=52.370216, lon=4.895168),
            RoutePoint(name="Bremen", lat=53.079296, lon=8.801694),
            RoutePoint(name="Copenhagen", lat=55.676098, lon=12.568337),
        ],
    )
    gpx = route_to_gpx(route)

    assert gpx.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert 'xmlns="http://www.topografix.com/GPX/1/1"' in gpx
    assert "<rte>" in gpx and "</rte>" in gpx
    assert gpx.count("<rtept") == 3
    assert 'lat="52.370216"' in gpx
    assert 'lon="12.568337"' in gpx
    assert "Amsterdam → Copenhagen" in gpx


def test_route_to_gpx_escapes_xml_special_characters_in_names():
    route = GetRouteOutput(
        origin="A&B<x>",
        destination='C"D',
        total_distance_km=10.0,
        suggested_days=1,
        waypoints=[RoutePoint(name="<bad>&name", lat=0.0, lon=0.0)],
    )
    gpx = route_to_gpx(route)

    assert "<bad>" not in gpx
    assert "&lt;bad&gt;" in gpx
    assert "&amp;name" in gpx
    assert "A&amp;B&lt;x&gt;" in gpx


def test_extract_latest_route_returns_none_when_history_has_no_get_route():
    history = [{"role": "user", "content": "Plan a trip"}]
    assert extract_latest_route(history) is None


def test_extract_latest_route_pairs_tool_use_with_matching_tool_result():
    route_payload = (
        '{"origin": "A", "destination": "B", "total_distance_km": 100.0, '
        '"suggested_days": 2, "waypoints": [{"name": "A", "lat": 1.0, "lon": 2.0}]}'
    )
    history = [
        {"role": "user", "content": "Plan A to B"},
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "u1", "name": "get_route", "input": {"origin": "A", "destination": "B"}},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "u1",
                    "is_error": False,
                    "content": [{"type": "text", "text": route_payload}],
                }
            ],
        },
    ]
    route = extract_latest_route(history)
    assert route is not None
    assert route.origin == "A"
    assert route.destination == "B"
    assert len(route.waypoints) == 1


def test_extract_latest_route_picks_most_recent_when_route_was_recomputed():
    first = (
        '{"origin": "A", "destination": "B", "total_distance_km": 100.0, '
        '"suggested_days": 2, "waypoints": [{"name": "A", "lat": 1.0, "lon": 2.0}]}'
    )
    second = (
        '{"origin": "X", "destination": "Y", "total_distance_km": 500.0, '
        '"suggested_days": 5, "waypoints": [{"name": "X", "lat": 9.0, "lon": 9.0}]}'
    )
    history = [
        {"role": "assistant", "content": [{"type": "tool_use", "id": "u1", "name": "get_route", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "u1", "is_error": False, "content": [{"type": "text", "text": first}]}]},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "u2", "name": "get_route", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "u2", "is_error": False, "content": [{"type": "text", "text": second}]}]},
    ]
    route = extract_latest_route(history)
    assert route is not None
    assert route.origin == "X"
    assert route.destination == "Y"


def test_extract_latest_route_returns_none_when_latest_call_errored():
    history = [
        {"role": "assistant", "content": [{"type": "tool_use", "id": "u1", "name": "get_route", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "u1", "is_error": True, "content": [{"type": "text", "text": '{"error": "bad input"}'}]}]},
    ]
    assert extract_latest_route(history) is None


def test_gpx_endpoint_returns_404_for_unknown_conversation():
    rt = _runtime(MockProvider())
    app.dependency_overrides[get_runtime] = lambda: rt
    try:
        client = TestClient(app)
        resp = client.get("/api/v1/conversations/does-not-exist/route.gpx")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Conversation not found."
    finally:
        app.dependency_overrides.pop(get_runtime, None)


def test_gpx_endpoint_returns_404_when_no_route_planned_yet():
    scripted = [MockResponse(content=[text_block("ack")], stop_reason=StopReason.END_TURN)]
    rt = _runtime(MockProvider(responses=scripted))
    app.dependency_overrides[get_runtime] = lambda: rt
    try:
        client = TestClient(app)
        first = client.post("/api/v1/chat", json={"message": "hello"})
        cid = first.json()["conversation_id"]

        resp = client.get(f"/api/v1/conversations/{cid}/route.gpx")
        assert resp.status_code == 404
        assert "No route" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_runtime, None)


def test_v0_route_gpx_is_stateless_and_returns_gpx_for_arbitrary_pair():
    rt = _runtime(MockProvider())
    app.dependency_overrides[get_runtime] = lambda: rt
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/v0/tools/route.gpx",
            json={"origin": "Berlin", "destination": "Prague"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith(GPX_MEDIA_TYPE)
        disposition = resp.headers["content-disposition"]
        assert "attachment" in disposition
        assert "berlin-to-prague.gpx" in disposition

        body = resp.text
        assert body.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert "<rte>" in body
        assert "Berlin → Prague" in body
        assert body.count("<rtept") >= 2
    finally:
        app.dependency_overrides.pop(get_runtime, None)


def test_v0_route_gpx_validates_input_via_pydantic():
    rt = _runtime(MockProvider())
    app.dependency_overrides[get_runtime] = lambda: rt
    try:
        client = TestClient(app)
        resp = client.post("/api/v0/tools/route.gpx", json={"origin": "B"})
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.pop(get_runtime, None)


def test_gpx_endpoint_serves_gpx_after_get_route_was_called():
    scripted = [
        MockResponse(
            content=[tool_use_block("u1", "get_route", {"origin": "Amsterdam", "destination": "Copenhagen"})],
            stop_reason=StopReason.TOOL_USE,
        ),
        MockResponse(content=[text_block("Done.")], stop_reason=StopReason.END_TURN),
    ]
    rt = _runtime(MockProvider(responses=scripted))
    app.dependency_overrides[get_runtime] = lambda: rt
    try:
        client = TestClient(app)
        chat_resp = client.post("/api/v1/chat", json={"message": "Plan Amsterdam to Copenhagen"})
        assert chat_resp.status_code == 200
        cid = chat_resp.json()["conversation_id"]

        gpx_resp = client.get(f"/api/v1/conversations/{cid}/route.gpx")
        assert gpx_resp.status_code == 200
        assert gpx_resp.headers["content-type"].startswith(GPX_MEDIA_TYPE)
        disposition = gpx_resp.headers["content-disposition"]
        assert "attachment" in disposition
        assert "amsterdam-to-copenhagen.gpx" in disposition

        body = gpx_resp.text
        assert body.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert "<rte>" in body
        assert "Amsterdam → Copenhagen" in body
        assert body.count("<rtept") >= 2
    finally:
        app.dependency_overrides.pop(get_runtime, None)
