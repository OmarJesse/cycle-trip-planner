from __future__ import annotations

from pydantic import BaseModel, Field


class RouteMockSettings(BaseModel):
    mock_coord_lat_min: float = Field(default=47.0, alias="MOCK_COORD_LAT_MIN")
    mock_coord_lat_span: float = Field(default=9.0, alias="MOCK_COORD_LAT_SPAN")
    mock_coord_lon_min: float = Field(default=4.0, alias="MOCK_COORD_LON_MIN")
    mock_coord_lon_span: float = Field(default=17.0, alias="MOCK_COORD_LON_SPAN")

    mock_route_distance_min_km: float = Field(default=450.0, alias="MOCK_ROUTE_DISTANCE_MIN_KM")
    mock_route_distance_span_km: float = Field(default=650.0, alias="MOCK_ROUTE_DISTANCE_SPAN_KM")
    mock_route_waypoint_count: int = Field(default=6, ge=2, le=20, alias="MOCK_ROUTE_WAYPOINT_COUNT")
    mock_route_default_daily_km: int = Field(default=100, ge=20, le=300, alias="MOCK_ROUTE_DEFAULT_DAILY_KM")
    mock_route_min_days: int = Field(default=2, ge=1, le=30, alias="MOCK_ROUTE_MIN_DAYS")

    mock_coord_decimals: int = Field(default=3, ge=0, le=6, alias="MOCK_COORD_DECIMALS")
    mock_route_distance_decimals: int = Field(default=2, ge=0, le=4, alias="MOCK_ROUTE_DISTANCE_DECIMALS")
    mock_route_distance_display_decimals: int = Field(default=1, ge=0, le=4, alias="MOCK_ROUTE_DISTANCE_DISPLAY_DECIMALS")
