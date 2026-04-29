import pytest

from src.agent.planning import build_day_by_day_plan, format_plan_markdown
from src.api.models import TripPreferences
from src.config.runtime import get_settings
from src.exception.errors import MissingPreferencesError


def _amsterdam_to_copenhagen(**overrides) -> TripPreferences:
    base = dict(
        origin="Amsterdam",
        destination="Copenhagen",
        daily_km=100,
        month="June",
        lodging_preference="camping",
        hostel_every_n_nights=4,
        nationality="Canadian",
        stay_days=10,
    )
    base.update(overrides)
    return TripPreferences(**base)


def test_plan_is_deterministic_for_same_preferences():
    plan_a = build_day_by_day_plan(_amsterdam_to_copenhagen())
    plan_b = build_day_by_day_plan(_amsterdam_to_copenhagen())
    assert [d.model_dump() for d in plan_a] == [d.model_dump() for d in plan_b]


def test_plan_day_count_respects_min_days_and_total_distance():
    settings = get_settings()
    prefs = _amsterdam_to_copenhagen(daily_km=100)
    plan = build_day_by_day_plan(prefs)
    assert len(plan) >= settings.plan_min_days
    total = sum(d.distance_km for d in plan)
    assert total > 0
    assert [d.day for d in plan] == list(range(1, len(plan) + 1))


def test_plan_segments_chain_endpoints_correctly():
    plan = build_day_by_day_plan(_amsterdam_to_copenhagen())
    assert plan[0].start == "Amsterdam"
    assert plan[-1].end == "Copenhagen"
    for prev, curr in zip(plan, plan[1:]):
        assert curr.start == prev.end


def test_plan_respects_hostel_cadence():
    prefs = _amsterdam_to_copenhagen(lodging_preference="camping", hostel_every_n_nights=4)
    plan = build_day_by_day_plan(prefs)
    for d in plan:
        sleep_lower = d.sleep.lower()
        if d.day % 4 == 0:
            assert "hostel" in sleep_lower, f"Day {d.day} expected hostel, got: {d.sleep}"
        else:
            assert "camping" in sleep_lower, f"Day {d.day} expected camping, got: {d.sleep}"


def test_plan_markdown_includes_required_sections_and_visa_note_when_known():
    prefs = _amsterdam_to_copenhagen()
    plan = build_day_by_day_plan(prefs)
    md = format_plan_markdown(plan, preferences=prefs)
    assert "## Trip summary" in md
    assert "## Day-by-day plan" in md
    assert "Budget" in md
    assert "Visa note" in md
    for d in plan:
        assert f"### Day {d.day}" in md


def test_plan_markdown_visa_prompt_when_nationality_missing():
    prefs = _amsterdam_to_copenhagen(nationality=None)
    plan = build_day_by_day_plan(prefs)
    md = format_plan_markdown(plan, preferences=prefs)
    assert "Tell me your nationality" in md


def test_plan_changes_when_daily_km_changes():
    fast = build_day_by_day_plan(_amsterdam_to_copenhagen(daily_km=120))
    slow = build_day_by_day_plan(_amsterdam_to_copenhagen(daily_km=80))
    assert len(slow) >= len(fast)


def test_plan_raises_on_missing_required_preferences():
    with pytest.raises(MissingPreferencesError):
        build_day_by_day_plan(TripPreferences(origin="Amsterdam"))
