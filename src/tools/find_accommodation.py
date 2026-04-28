from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field


class AccommodationOption(BaseModel):
    kind: Literal["camping", "hostel", "hotel"]
    name: str
    approx_price_eur: int
    distance_from_target_km: float


class FindAccommodationInput(BaseModel):
    near: str = Field(min_length=2, description="City or waypoint name")
    kind: Literal["camping", "hostel", "hotel", "any"] = "any"


class FindAccommodationOutput(BaseModel):
    near: str
    options: list[AccommodationOption]


def find_accommodation(inp: FindAccommodationInput) -> FindAccommodationOutput:
    # Deterministic mock options
    base = int(hashlib.sha256(inp.near.encode("utf-8")).hexdigest()[:8], 16) % 100

    def opt(kind: str, idx: int, price: int) -> AccommodationOption:
        dist = round(((base + idx * 7) % 40) / 10.0, 1)  # 0.0..3.9
        return AccommodationOption(
            kind=kind, name=f"{inp.near} {kind.title()} {idx}", approx_price_eur=price, distance_from_target_km=dist
        )

    all_opts = [
        opt("camping", 1, 18 + (base % 10)),
        opt("camping", 2, 22 + (base % 12)),
        opt("hostel", 1, 35 + (base % 15)),
        opt("hostel", 2, 42 + (base % 18)),
        opt("hotel", 1, 85 + (base % 25)),
        opt("hotel", 2, 110 + (base % 40)),
    ]

    if inp.kind == "any":
        options = all_opts
    else:
        options = [o for o in all_opts if o.kind == inp.kind]

    return FindAccommodationOutput(near=inp.near, options=options)

