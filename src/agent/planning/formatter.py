from __future__ import annotations

from src.api.models import DayPlan, TripPreferences
from src.config.runtime import get_settings
from src.tools.builtins import build_registry
from src.tools.names import ToolName


def format_plan_markdown(
    plan: list[DayPlan],
    *,
    preferences: TripPreferences | None = None,
) -> str:
    lines: list[str] = []
    if preferences and preferences.origin and preferences.destination:
        lines.extend(_header_lines(plan, preferences))
        lines.append("")

    lines.append("## Day-by-day plan")
    for d in plan:
        lines.extend(_day_lines(d))

    return "\n".join(lines).strip()


def _header_lines(plan: list[DayPlan], preferences: TripPreferences) -> list[str]:
    s = get_settings()
    lines = [f"## Trip summary: {preferences.origin} → {preferences.destination}"]

    if preferences.daily_km:
        lines.append(f"- **Target pace**: ~{preferences.daily_km} km/day")
    if preferences.month:
        lines.append(f"- **Month**: {preferences.month}")
    if preferences.lodging_preference:
        cadence = (
            f", hostel every {preferences.hostel_every_n_nights} nights"
            if preferences.hostel_every_n_nights
            else ""
        )
        lines.append(f"- **Lodging**: {preferences.lodging_preference}{cadence}")

    budget_line = _budget_line(plan, preferences, s.plan_food_style, s.mock_route_default_daily_km)
    if budget_line:
        lines.append(budget_line)

    visa_line = _visa_line(plan, preferences)
    if visa_line:
        lines.append(visa_line)

    return lines


def _budget_line(
    plan: list[DayPlan],
    preferences: TripPreferences,
    food_style: str,
    default_daily_km: int,
) -> str | None:
    try:
        registry = build_registry()
        budget = registry.dispatch(
            ToolName.ESTIMATE_BUDGET,
            {
                "days": len(plan),
                "daily_distance_km": preferences.daily_km or default_daily_km,
                "lodging_style": preferences.lodging_preference,
                "food_style": food_style,
            },
        )
        return f"- **Budget**: ~{budget.currency} {budget.estimated_total} total for {budget.days} days"
    except Exception:
        return None


def _visa_line(plan: list[DayPlan], preferences: TripPreferences) -> str | None:
    if not preferences.nationality:
        return "- **Visa note**: Tell me your nationality and expected stay duration if you want a visa check."
    try:
        registry = build_registry()
        visa = registry.dispatch(
            ToolName.CHECK_VISA_REQUIREMENTS,
            {
                "nationality": preferences.nationality,
                "destination_country": preferences.destination,
                "stay_days": preferences.stay_days or len(plan),
            },
        )
        return f"- **Visa note**: {visa.requirement} — {visa.notes}"
    except Exception:
        return None


def _day_lines(d: DayPlan) -> list[str]:
    lines = [
        f"### Day {d.day}: {d.start} → {d.end}",
        f"- **Distance**: {d.distance_km} km",
        f"- **Terrain**: {d.elevation_gain_m} m gain ({d.difficulty})",
        f"- **Weather**: {d.weather_summary}",
        f"- **Sleep**: {d.sleep}",
    ]
    if d.highlights:
        lines.append(f"- **Highlights**: {', '.join(d.highlights)}")
    lines.append("")
    return lines
