from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field

from src.config.runtime import get_settings


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
    s = get_settings()
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    coord_scale = 10 ** s.mock_coord_decimals
    lat = s.mock_coord_lat_min + (int(h[:8], 16) % int(s.mock_coord_lat_span * coord_scale)) / coord_scale
    lon = s.mock_coord_lon_min + (int(h[8:16], 16) % int(s.mock_coord_lon_span * coord_scale)) / coord_scale
    return lat, lon


def get_route(inp: GetRouteInput) -> GetRouteOutput:
    s = get_settings()
    h = int(hashlib.sha256(f"{inp.origin}->{inp.destination}".encode("utf-8")).hexdigest()[:8], 16)
    distance_scale = 10 ** s.mock_route_distance_decimals
    total_distance_km = s.mock_route_distance_min_km + (h % int(s.mock_route_distance_span_km * distance_scale)) / distance_scale

    n = s.mock_route_waypoint_count
    mid = [f"Waypoint_{i}" for i in range(1, max(0, n - 2) + 1)]
    points = [inp.origin, *mid, inp.destination]
    waypoints: list[RoutePoint] = []
    for p in points:
        lat, lon = _fake_coord(f"{inp.origin}|{inp.destination}|{p}")
        waypoints.append(RoutePoint(name=p, lat=lat, lon=lon))

    suggested_days = max(s.mock_route_min_days, round(total_distance_km / float(s.mock_route_default_daily_km)))
    return GetRouteOutput(
        origin=inp.origin,
        destination=inp.destination,
        total_distance_km=round(total_distance_km, s.mock_route_distance_display_decimals),
        waypoints=waypoints,
        suggested_days=suggested_days,
    )

