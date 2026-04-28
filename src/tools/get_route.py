from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field


class RoutePoint(BaseModel):
    name: str
    lat: float
    lon: float


class GetRouteInput(BaseModel):
    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    mode: Literal["cycling"] = "cycling"


class GetRouteOutput(BaseModel):
    origin: str
    destination: str
    total_distance_km: float
    waypoints: list[RoutePoint]
    suggested_days: int


def _fake_coord(seed: str) -> tuple[float, float]:
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    # Map to Europe-ish bounding box (roughly)
    lat = 47.0 + (int(h[:8], 16) % 9000) / 1000.0  # 47..56
    lon = 4.0 + (int(h[8:16], 16) % 17000) / 1000.0  # 4..21
    return lat, lon


def get_route(inp: GetRouteInput) -> GetRouteOutput:
    # Deterministic mock: distance derived from hash (but within plausible range)
    h = int(hashlib.sha256(f"{inp.origin}->{inp.destination}".encode("utf-8")).hexdigest()[:8], 16)
    total_distance_km = 450.0 + (h % 65000) / 100.0  # 450..1100

    # Create 6 intermediate waypoints including endpoints
    points = [inp.origin, "Waypoint_1", "Waypoint_2", "Waypoint_3", "Waypoint_4", inp.destination]
    waypoints: list[RoutePoint] = []
    for p in points:
        lat, lon = _fake_coord(f"{inp.origin}|{inp.destination}|{p}")
        waypoints.append(RoutePoint(name=p, lat=lat, lon=lon))

    suggested_days = max(2, round(total_distance_km / 100.0))
    return GetRouteOutput(
        origin=inp.origin,
        destination=inp.destination,
        total_distance_km=round(total_distance_km, 1),
        waypoints=waypoints,
        suggested_days=suggested_days,
    )

