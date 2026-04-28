from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field


class PointsOfInterestInput(BaseModel):
    near: str = Field(min_length=2, description="City or waypoint name")
    category: Literal["sights", "food", "bike_shops", "nature", "museums", "any"] = "any"
    limit: int = Field(default=6, ge=1, le=20)


class PointOfInterest(BaseModel):
    name: str
    category: str
    note: str


class PointsOfInterestOutput(BaseModel):
    near: str
    category: str
    items: list[PointOfInterest]


def get_points_of_interest(inp: PointsOfInterestInput) -> PointsOfInterestOutput:
    seed = int(hashlib.sha256(f"{inp.near}|{inp.category}".encode("utf-8")).hexdigest()[:8], 16)
    categories = ["sights", "food", "bike_shops", "nature", "museums"]
    cat = inp.category if inp.category != "any" else categories[seed % len(categories)]

    items: list[PointOfInterest] = []
    for i in range(inp.limit):
        n = (seed + i * 97) % 1000
        items.append(
            PointOfInterest(
                name=f"{inp.near} {cat.replace('_', ' ').title()} #{i+1}",
                category=cat,
                note=f"Mock suggestion (id {n}) — good for a short stop.",
            )
        )

    return PointsOfInterestOutput(near=inp.near, category=cat, items=items)

