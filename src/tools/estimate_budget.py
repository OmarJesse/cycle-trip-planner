from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.config.runtime import get_settings


class EstimateBudgetInput(BaseModel):
    days: int = Field(ge=1, le=90)
    daily_distance_km: int = Field(ge=20, le=300)
    lodging_style: Literal["camping", "hostel", "hotel", "mixed"] = "mixed"
    food_style: Literal["budget", "balanced", "treats"] = "balanced"


class EstimateBudgetOutput(BaseModel):
    days: int
    currency: str
    estimated_total: int
    breakdown_per_day: dict[str, int]
    notes: str


def estimate_budget(inp: EstimateBudgetInput) -> EstimateBudgetOutput:
    s = get_settings()
    lodging = {
        "camping": s.mock_budget_lodging_camping,
        "hostel": s.mock_budget_lodging_hostel,
        "hotel": s.mock_budget_lodging_hotel,
        "mixed": s.mock_budget_lodging_mixed,
    }[inp.lodging_style]
    food = {
        "budget": s.mock_budget_food_budget,
        "balanced": s.mock_budget_food_balanced,
        "treats": s.mock_budget_food_treats,
    }[inp.food_style]

    variable = int(round(inp.daily_distance_km * float(s.mock_budget_variable_per_km)))

    per_day = {
        "lodging": lodging,
        "food": food,
        "snacks_maintenance": variable,
        "misc": s.mock_budget_misc_per_day,
    }
    total = inp.days * sum(per_day.values())
    return EstimateBudgetOutput(
        days=inp.days,
        currency=s.mock_budget_currency,
        estimated_total=int(round(total)),
        breakdown_per_day=per_day,
        notes="Estimate based on configured daily rates; verify with current local prices.",
    )

