from src.agent.planning import build_day_by_day_plan, format_plan_markdown
from src.api.models import TripPreferences


def test_golden_deterministic_plan_smoke():
    prefs = TripPreferences(
        origin="Amsterdam",
        destination="Copenhagen",
        daily_km=100,
        month="June",
        lodging_preference="camping",
        hostel_every_n_nights=4,
        nationality="Canadian",
        stay_days=10,
    )
    plan = build_day_by_day_plan(prefs)
    md = format_plan_markdown(plan, preferences=prefs)
    assert "Day-by-day plan" in md
    assert "Budget (mock)" in md
    assert "Visa note" in md

