from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.api.models import DayPlan, TripPreferences
from src.tools.builtins import build_registry


@dataclass(frozen=True)
class Segment:
    start: str
    end: str
    distance_km: float


def split_into_daily_segments(origin: str, destination: str, total_distance_km: float, daily_km: int) -> list[Segment]:
    days = max(1, int(round(total_distance_km / max(1, daily_km))))
    if days < 2:
        days = 2
    base = total_distance_km / days
    segments: list[Segment] = []
    prev = origin
    for i in range(1, days + 1):
        nxt = destination if i == days else f"Day{i}_Stop"
        segments.append(Segment(start=prev, end=nxt, distance_km=round(base, 1)))
        prev = nxt
    return segments


def lodging_kind_for_night(preferences: TripPreferences, day: int) -> Literal["camping", "hostel", "hotel", "any"]:
    pref = preferences.lodging_preference
    if preferences.hostel_every_n_nights and day % preferences.hostel_every_n_nights == 0:
        return "hostel"
    if pref == "mixed":
        return "any"
    return pref


def build_day_by_day_plan(preferences: TripPreferences) -> list[DayPlan]:
    """
    Deterministic planner using the mock tools.
    Used both for non-LLM fallback and as a reference format.
    """
    if not (preferences.origin and preferences.destination and preferences.daily_km and preferences.month):
        raise ValueError("Missing required preferences to build a plan.")

    registry = build_registry()
    route = registry.dispatch(
        "get_route",
        {"origin": preferences.origin, "destination": preferences.destination, "mode": "cycling"},
    )

    segments = split_into_daily_segments(
        preferences.origin, preferences.destination, route.total_distance_km, preferences.daily_km
    )

    plans: list[DayPlan] = []
    for idx, seg in enumerate(segments, start=1):
        elev = registry.dispatch(
            "get_elevation_profile",
            {"origin": seg.start, "destination": seg.end, "distance_km": seg.distance_km},
        )
        weather = registry.dispatch("get_weather", {"location": seg.end, "month": preferences.month})

        kind = lodging_kind_for_night(preferences, idx)
        acc = registry.dispatch("find_accommodation", {"near": seg.end, "kind": kind})
        sleep = (
            f"{acc.options[0].kind.title()}: {acc.options[0].name} (~€{acc.options[0].approx_price_eur})"
            if acc.options
            else "No accommodation options found."
        )

        pois = registry.dispatch("get_points_of_interest", {"near": seg.end, "category": "any", "limit": 4})
        highlights = [p.name for p in getattr(pois, "items", [])][:4]

        plans.append(
            DayPlan(
                day=idx,
                start=seg.start,
                end=seg.end,
                distance_km=seg.distance_km,
                elevation_gain_m=elev.elevation_gain_m,
                difficulty=elev.difficulty,
                weather_summary=f"{weather.summary} (avg {weather.avg_low_c}–{weather.avg_high_c}°C)",
                sleep=sleep,
                highlights=highlights,
            )
        )

    return plans


def format_plan_markdown(plan: list[DayPlan], *, preferences: TripPreferences | None = None) -> str:
    lines: list[str] = []
    if preferences and preferences.origin and preferences.destination:
        lines.append(f"## Trip summary: {preferences.origin} → {preferences.destination}")
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

        # Optional: budget + visa
        try:
            reg = build_registry()
            budget = reg.dispatch(
                "estimate_budget",
                {
                    "days": len(plan),
                    "daily_distance_km": preferences.daily_km or 100,
                    "lodging_style": preferences.lodging_preference,
                    "food_style": "balanced",
                },
            )
            lines.append(f"- **Budget (mock)**: ~€{budget.estimated_total} total for {budget.days} days")
        except Exception:
            pass

        if preferences.nationality:
            try:
                reg = build_registry()
                visa = reg.dispatch(
                    "check_visa_requirements",
                    {
                        "nationality": preferences.nationality,
                        "destination_country": preferences.destination,
                        "stay_days": preferences.stay_days or len(plan),
                    },
                )
                lines.append(f"- **Visa note (mock)**: {visa.requirement} — {visa.notes}")
            except Exception:
                pass
        else:
            lines.append("- **Visa note**: Tell me your nationality and expected stay duration if you want a visa check.")

        lines.append("")

    lines.append("## Day-by-day plan")
    for d in plan:
        lines.append(f"### Day {d.day}: {d.start} → {d.end}")
        lines.append(f"- **Distance**: {d.distance_km} km")
        lines.append(f"- **Terrain**: {d.elevation_gain_m} m gain ({d.difficulty})")
        lines.append(f"- **Weather**: {d.weather_summary}")
        lines.append(f"- **Sleep**: {d.sleep}")
        if d.highlights:
            lines.append(f"- **Highlights**: {', '.join(d.highlights)}")
        lines.append("")
    return "\n".join(lines).strip()

