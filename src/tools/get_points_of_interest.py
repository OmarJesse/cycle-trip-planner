from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field

from src.config.runtime import get_settings


class PointsOfInterestInput(BaseModel):
    near: str = Field(min_length=2, description="City or waypoint name")
    category: Literal["sights", "food", "bike_shops", "nature", "museums", "any"] = "any"
    limit: int = Field(default_factory=lambda: get_settings().mock_poi_default_limit, ge=1, le=20)


class PointOfInterest(BaseModel):
    name: str
    category: str


class PointsOfInterestOutput(BaseModel):
    near: str
    category: str
    items: list[PointOfInterest]


def get_points_of_interest(inp: PointsOfInterestInput) -> PointsOfInterestOutput:
    s = get_settings()
    seed = int(hashlib.sha256(f"{inp.near}|{inp.category}".encode("utf-8")).hexdigest()[:8], 16)
    categories = s.mock_poi_categories
    cat = inp.category if inp.category != "any" else categories[seed % len(categories)]

    items = [
        PointOfInterest(
            name=f"{inp.near} {cat.replace('_', ' ').title()} #{i + 1}",
            category=cat,
        )
        for i in range(inp.limit)
    ]
    return PointsOfInterestOutput(near=inp.near, category=cat, items=items)
