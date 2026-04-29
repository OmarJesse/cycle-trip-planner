from __future__ import annotations

from src.agent.planning.day import build_day_plan
from src.agent.planning.route import fetch_route
from src.agent.planning.segments import split_into_daily_segments
from src.api.models import DayPlan, TripPreferences
from src.config.runtime import get_settings
from src.exception.errors import MissingPreferencesError
from src.tools.builtins import build_registry


def build_day_by_day_plan(preferences: TripPreferences) -> list[DayPlan]:
    _validate_preferences(preferences)

    settings = get_settings()
    registry = build_registry()

    route = fetch_route(preferences, registry)
    segments = split_into_daily_segments(
        preferences.origin,
        preferences.destination,
        route.total_distance_km,
        preferences.daily_km,
        min_days=settings.plan_min_days,
        distance_decimals=settings.plan_distance_decimals,
    )

    return [
        build_day_plan(
            index=idx,
            segment=segment,
            preferences=preferences,
            registry=registry,
            settings=settings,
        )
        for idx, segment in enumerate(segments, start=1)
    ]


def _validate_preferences(preferences: TripPreferences) -> None:
    if not (preferences.origin and preferences.destination and preferences.daily_km and preferences.month):
        raise MissingPreferencesError("Missing required preferences to build a plan.")
