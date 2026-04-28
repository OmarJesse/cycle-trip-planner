from __future__ import annotations

from enum import StrEnum


class ToolName(StrEnum):
    GET_ROUTE = "get_route"
    FIND_ACCOMMODATION = "find_accommodation"
    GET_WEATHER = "get_weather"
    GET_ELEVATION_PROFILE = "get_elevation_profile"
    GET_POINTS_OF_INTEREST = "get_points_of_interest"
    CHECK_VISA_REQUIREMENTS = "check_visa_requirements"
    ESTIMATE_BUDGET = "estimate_budget"
