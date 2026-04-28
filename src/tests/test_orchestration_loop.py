from __future__ import annotations

from src.agent.orchestration import run_agent_loop
from src.agent.providers.base import StopReason
from src.agent.providers.mock_provider import MockProvider, MockResponse, text_block, tool_use_block
from src.tools.builtins import build_registry


def _run(provider, registry, messages, *, max_rounds=10, max_tokens=512):
    return run_agent_loop(
        system="test system prompt",
        tools=registry.schemas_for_llm(),
        messages=messages,
        registry=registry,
        provider=provider,
        max_rounds=max_rounds,
        max_tokens=max_tokens,
    )


def test_orchestration_runs_multi_step_tool_use_and_returns_final_text():
    registry = build_registry()
    scripted = [
        MockResponse(
            content=[
                text_block("Pulling the route."),
                tool_use_block("u1", "get_route", {"origin": "Amsterdam", "destination": "Copenhagen"}),
            ],
            stop_reason=StopReason.TOOL_USE,
        ),
        MockResponse(
            content=[
                tool_use_block("u2", "get_weather", {"location": "Copenhagen", "month": "June"}),
            ],
            stop_reason=StopReason.TOOL_USE,
        ),
        MockResponse(
            content=[
                tool_use_block("u3", "find_accommodation", {"near": "Copenhagen", "kind": "camping"}),
            ],
            stop_reason=StopReason.TOOL_USE,
        ),
        MockResponse(
            content=[text_block("Here is your itinerary: ...")],
            stop_reason=StopReason.END_TURN,
        ),
    ]
    provider = MockProvider(responses=scripted)

    result = _run(provider, registry, [{"role": "user", "content": "Plan Amsterdam to Copenhagen"}])

    assert result.error is None
    assert result.truncated is False
    assert result.rounds == 4
    assert result.reply == "Here is your itinerary: ..."

    names = [t.name for t in result.tool_calls]
    assert names == ["get_route", "get_weather", "find_accommodation"]

    route_call = result.tool_calls[0]
    assert route_call.is_error is False
    assert route_call.output is not None
    assert route_call.output["origin"] == "Amsterdam"
    assert route_call.output["destination"] == "Copenhagen"
    assert route_call.output["total_distance_km"] > 0


def test_orchestration_truncates_when_loop_exceeds_max_rounds():
    registry = build_registry()
    looping = MockResponse(
        content=[tool_use_block("u", "get_route", {"origin": "A", "destination": "B"})],
        stop_reason=StopReason.TOOL_USE,
    )
    provider = MockProvider(responses=[looping] * 10)

    result = _run(provider, registry, [{"role": "user", "content": "loop forever"}], max_rounds=3, max_tokens=128)

    assert result.truncated is True
    assert result.rounds == 3
    assert "round limit" in result.reply.lower()
    assert len(result.tool_calls) == 3


def test_orchestration_translates_provider_errors_via_handler():
    from src.agent.providers.base import LLMProvider, LLMResponse

    class _BoomProvider(LLMProvider):
        def create_message(self, **kwargs) -> LLMResponse:
            raise RuntimeError("upstream blew up")

    result = _run(_BoomProvider(), build_registry(), [{"role": "user", "content": "hi"}], max_rounds=3, max_tokens=128)

    assert result.error == "upstream blew up"
    assert result.rounds == 0
    assert "LLM API error" in result.reply
    assert result.tool_calls == []


def test_orchestration_records_tool_validation_errors():
    registry = build_registry()
    scripted = [
        MockResponse(
            content=[tool_use_block("u1", "get_route", {"origin": "X"})],
            stop_reason=StopReason.TOOL_USE,
        ),
        MockResponse(content=[text_block("Sorry, missing destination.")], stop_reason=StopReason.END_TURN),
    ]
    provider = MockProvider(responses=scripted)

    result = _run(provider, registry, [{"role": "user", "content": "broken"}], max_rounds=4, max_tokens=128)

    assert result.tool_calls[0].is_error is True
    assert result.tool_calls[0].output is None
    assert result.reply == "Sorry, missing destination."


def test_registry_emits_cache_breakpoint_only_when_requested():
    registry = build_registry()

    plain = registry.schemas_for_llm()
    assert all("cache_control" not in s for s in plain)

    cached = registry.schemas_for_llm(cache_breakpoint=True)
    assert all("cache_control" not in s for s in cached[:-1])
    assert cached[-1]["cache_control"] == {"type": "ephemeral"}
