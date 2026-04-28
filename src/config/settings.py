from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderName(str, Enum):
    anthropic = "anthropic"
    gemini = "gemini"
    mock = "mock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_title: str = "Cycling Trip Planner Agent"
    api_version: str = "1.0.0"

    llm_provider: LLMProviderName = Field(default=LLMProviderName.anthropic, alias="LLM_PROVIDER")
    llm_model: str = Field(default="claude-3-haiku-20240307", alias="LLM_MODEL")

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    max_tool_rounds: int = Field(default=6, ge=1, le=20, alias="MAX_TOOL_ROUNDS")
    max_tokens: int = Field(default=900, ge=64, le=4096, alias="MAX_TOKENS")

    include_structured_plan: bool = Field(default=True, alias="INCLUDE_STRUCTURED_PLAN")
    enable_optional_tools: bool = Field(default=True, alias="ENABLE_OPTIONAL_TOOLS")

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"], alias="CORS_ALLOW_ORIGINS")

    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=60, ge=1, le=100000, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600, alias="RATE_LIMIT_WINDOW_SECONDS")

    mock_coord_lat_min: float = Field(default=47.0, alias="MOCK_COORD_LAT_MIN")
    mock_coord_lat_span: float = Field(default=9.0, alias="MOCK_COORD_LAT_SPAN")
    mock_coord_lon_min: float = Field(default=4.0, alias="MOCK_COORD_LON_MIN")
    mock_coord_lon_span: float = Field(default=17.0, alias="MOCK_COORD_LON_SPAN")

    mock_route_distance_min_km: float = Field(default=450.0, alias="MOCK_ROUTE_DISTANCE_MIN_KM")
    mock_route_distance_span_km: float = Field(default=650.0, alias="MOCK_ROUTE_DISTANCE_SPAN_KM")
    mock_route_waypoint_count: int = Field(default=6, ge=2, le=20, alias="MOCK_ROUTE_WAYPOINT_COUNT")
    mock_route_default_daily_km: int = Field(default=100, ge=20, le=300, alias="MOCK_ROUTE_DEFAULT_DAILY_KM")
    mock_route_min_days: int = Field(default=2, ge=1, le=30, alias="MOCK_ROUTE_MIN_DAYS")

    mock_accommodation_seed_mod: int = Field(default=100, ge=10, le=10000, alias="MOCK_ACCOMMODATION_SEED_MOD")
    mock_accommodation_dist_mod: int = Field(default=40, ge=1, le=1000, alias="MOCK_ACCOMMODATION_DIST_MOD")
    mock_accommodation_dist_scale: float = Field(default=10.0, gt=0, alias="MOCK_ACCOMMODATION_DIST_SCALE")
    mock_accommodation_dist_step: int = Field(default=7, ge=1, le=100, alias="MOCK_ACCOMMODATION_DIST_STEP")

    mock_price_camping_base: int = Field(default=18, ge=0, alias="MOCK_PRICE_CAMPING_BASE")
    mock_price_camping_span: int = Field(default=12, ge=0, alias="MOCK_PRICE_CAMPING_SPAN")
    mock_price_hostel_base: int = Field(default=35, ge=0, alias="MOCK_PRICE_HOSTEL_BASE")
    mock_price_hostel_span: int = Field(default=20, ge=0, alias="MOCK_PRICE_HOSTEL_SPAN")
    mock_price_hotel_base: int = Field(default=85, ge=0, alias="MOCK_PRICE_HOTEL_BASE")
    mock_price_hotel_span: int = Field(default=40, ge=0, alias="MOCK_PRICE_HOTEL_SPAN")

    mock_weather_high_base_c: int = Field(default=16, ge=-50, le=60, alias="MOCK_WEATHER_HIGH_BASE_C")
    mock_weather_high_span_c: int = Field(default=12, ge=0, le=60, alias="MOCK_WEATHER_HIGH_SPAN_C")
    mock_weather_low_delta_base_c: int = Field(default=6, ge=0, le=40, alias="MOCK_WEATHER_LOW_DELTA_BASE_C")
    mock_weather_low_delta_span_c: int = Field(default=3, ge=0, le=40, alias="MOCK_WEATHER_LOW_DELTA_SPAN_C")
    mock_weather_rain_base_mm: int = Field(default=35, ge=0, le=1000, alias="MOCK_WEATHER_RAIN_BASE_MM")
    mock_weather_rain_span_mm: int = Field(default=70, ge=0, le=1000, alias="MOCK_WEATHER_RAIN_SPAN_MM")

    mock_elev_hash_mod_m: int = Field(default=1800, ge=1, le=100000, alias="MOCK_ELEV_HASH_MOD_M")
    mock_elev_gain_per_km: float = Field(default=4.0, ge=0, alias="MOCK_ELEV_GAIN_PER_KM")
    mock_elev_easy_max_m: int = Field(default=900, ge=0, alias="MOCK_ELEV_EASY_MAX_M")
    mock_elev_moderate_max_m: int = Field(default=1800, ge=0, alias="MOCK_ELEV_MODERATE_MAX_M")

    mock_poi_categories: list[str] = Field(
        default_factory=lambda: ["sights", "food", "bike_shops", "nature", "museums"],
        alias="MOCK_POI_CATEGORIES",
    )
    mock_poi_default_limit: int = Field(default=6, ge=1, le=20, alias="MOCK_POI_DEFAULT_LIMIT")
    mock_poi_seed_mod: int = Field(default=1000, ge=1, le=1000000, alias="MOCK_POI_SEED_MOD")
    mock_poi_step: int = Field(default=97, ge=1, le=10000, alias="MOCK_POI_STEP")

    mock_budget_lodging_camping: int = Field(default=18, ge=0, alias="MOCK_BUDGET_LODGING_CAMPING")
    mock_budget_lodging_hostel: int = Field(default=40, ge=0, alias="MOCK_BUDGET_LODGING_HOSTEL")
    mock_budget_lodging_hotel: int = Field(default=100, ge=0, alias="MOCK_BUDGET_LODGING_HOTEL")
    mock_budget_lodging_mixed: int = Field(default=45, ge=0, alias="MOCK_BUDGET_LODGING_MIXED")
    mock_budget_food_budget: int = Field(default=18, ge=0, alias="MOCK_BUDGET_FOOD_BUDGET")
    mock_budget_food_balanced: int = Field(default=28, ge=0, alias="MOCK_BUDGET_FOOD_BALANCED")
    mock_budget_food_treats: int = Field(default=40, ge=0, alias="MOCK_BUDGET_FOOD_TREATS")
    mock_budget_variable_per_km: float = Field(default=0.12, ge=0, alias="MOCK_BUDGET_VARIABLE_PER_KM")
    mock_budget_misc_per_day: int = Field(default=8, ge=0, alias="MOCK_BUDGET_MISC_PER_DAY")
    mock_budget_currency: str = Field(default="EUR", alias="MOCK_BUDGET_CURRENCY")

    plan_poi_per_day: int = Field(default=4, ge=0, le=20, alias="PLAN_POI_PER_DAY")
    plan_food_style: str = Field(default="balanced", alias="PLAN_FOOD_STYLE")

    mock_visa_schengen_countries: list[str] = Field(
        default_factory=lambda: ["netherlands", "denmark", "germany", "belgium", "france", "sweden", "norway"],
        alias="MOCK_VISA_SCHENGEN_COUNTRIES",
    )
    mock_visa_max_days_no_visa: int = Field(default=90, ge=1, le=365, alias="MOCK_VISA_MAX_DAYS_NO_VISA")

