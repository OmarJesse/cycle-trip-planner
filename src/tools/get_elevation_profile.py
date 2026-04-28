from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field


class GetElevationProfileInput(BaseModel):
    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    distance_km: float = Field(gt=0)


class GetElevationProfileOutput(BaseModel):
    origin: str
    destination: str
    elevation_gain_m: int
    difficulty: Literal["easy", "moderate", "hard"]


def get_elevation_profile(inp: GetElevationProfileInput) -> GetElevationProfileOutput:
    h = int(hashlib.sha256(f"{inp.origin}->{inp.destination}".encode("utf-8")).hexdigest()[:8], 16)
    gain = int((h % 1800) + inp.distance_km * 4)  # distance influences gain
    if gain < 900:
        difficulty = "easy"
    elif gain < 1800:
        difficulty = "moderate"
    else:
        difficulty = "hard"
    return GetElevationProfileOutput(
        origin=inp.origin,
        destination=inp.destination,
        elevation_gain_m=gain,
        difficulty=difficulty,
    )

