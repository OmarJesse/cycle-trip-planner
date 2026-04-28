from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EstimateBudgetInput(BaseModel):
    days: int = Field(ge=1, le=90)
    daily_distance_km: int = Field(ge=20, le=300)
    lodging_style: Literal["camping", "hostel", "hotel", "mixed"] = "mixed"
    food_style: Literal["budget", "balanced", "treats"] = "balanced"


class EstimateBudgetOutput(BaseModel):
    days: int
    currency: Literal["EUR"] = "EUR"
    estimated_total: int
    breakdown_per_day: dict[str, int]
    notes: str


def estimate_budget(inp: EstimateBudgetInput) -> EstimateBudgetOutput:
    # Mock assumptions in EUR/day
    lodging = {
        "camping": 18,
        "hostel": 40,
        "hotel": 100,
        "mixed": 45,
    }[inp.lodging_style]
    food = {"budget": 18, "balanced": 28, "treats": 40}[inp.food_style]

    # Small variable cost: snacks/maintenance scale with distance
    variable = int(round(inp.daily_distance_km * 0.12))  # ~€12 at 100km

    per_day = {
        "lodging": lodging,
        "food": food,
        "snacks_maintenance": variable,
        "misc": 8,
    }
    total = inp.days * sum(per_day.values())
    return EstimateBudgetOutput(
        days=inp.days,
        estimated_total=int(total),
        breakdown_per_day=per_day,
        notes="Mock budget estimate in EUR. Real costs vary by country, season, and booking flexibility.",
    )

