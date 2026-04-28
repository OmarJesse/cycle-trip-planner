from __future__ import annotations

from src.agent.planning.lodging import lodging_kind_for_night
from src.agent.planning.segments import split_into_daily_segments
from src.api.models import DayPlan, TripPreferences
from src.config.runtime import get_settings
from src.tools.builtins import build_registry
from src.tools.names import ToolName


def build_day_by_day_plan(preferences: TripPreferences) -> list[DayPlan]:
    if not (preferences.origin and preferences.destination and preferences.daily_km and preferences.month):
        raise ValueError("Missing required preferences to build a plan.")

    s = get_settings()
    registry = build_registry()

    route = registry.dispatch(
        ToolName.GET_ROUTE,
        {"origin": preferences.origin, "destination": preferences.destination, "mode": "cycling"},
    )

    segments = split_into_daily_segments(
        preferences.origin,
        preferences.destination,
        route.total_distance_km,
        preferences.daily_km,
    )

    plans: list[DayPlan] = []
    for idx, seg in enumerate(segments, start=1):
        elev = registry.dispatch(
            ToolName.GET_ELEVATION_PROFILE,
            {"origin": seg.start, "destination": seg.end, "distance_km": seg.distance_km},
        )
        weather = registry.dispatch(
            ToolName.GET_WEATHER,
            {"location": seg.end, "month": preferences.month},
        )

        kind = lodging_kind_for_night(preferences, idx)
        acc = registry.dispatch(ToolName.FIND_ACCOMMODATION, {"near": seg.end, "kind": kind})
        sleep = (
            f"{acc.options[0].kind.title()}: {acc.options[0].name} (~€{acc.options[0].approx_price_eur})"
            if acc.options
            else "No accommodation options found."
        )

        pois = registry.dispatch(
            ToolName.GET_POINTS_OF_INTEREST,
            {"near": seg.end, "category": "any", "limit": int(s.plan_poi_per_day)},
        )
        highlights = [p.name for p in getattr(pois, "items", [])][: int(s.plan_poi_per_day)]

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
