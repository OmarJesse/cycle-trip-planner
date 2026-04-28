from __future__ import annotations

from src.tools.find_accommodation import (
    FindAccommodationInput,
    FindAccommodationOutput,
    find_accommodation,
)
from src.tools.get_elevation_profile import (
    GetElevationProfileInput,
    GetElevationProfileOutput,
    get_elevation_profile,
)
from src.tools.get_route import GetRouteInput, GetRouteOutput, get_route
from src.tools.get_weather import GetWeatherInput, GetWeatherOutput, get_weather
from src.tools.get_points_of_interest import (
    PointsOfInterestInput,
    PointsOfInterestOutput,
    get_points_of_interest,
)
from src.tools.check_visa_requirements import (
    VisaRequirementsInput,
    VisaRequirementsOutput,
    check_visa_requirements,
)
from src.tools.estimate_budget import (
    EstimateBudgetInput,
    EstimateBudgetOutput,
    estimate_budget,
)
from src.tools.registry import ToolRegistry, ToolSpec


def build_registry() -> ToolRegistry:
    tools = [
        ToolSpec(
            name="get_route",
            description="Get a cycling route between two points: total distance, suggested days, and waypoints.",
            input_model=GetRouteInput,
            output_model=GetRouteOutput,
            handler=get_route,
        ),
        ToolSpec(
            name="find_accommodation",
            description="Find places to stay near a location (camping, hostels, hotels).",
            input_model=FindAccommodationInput,
            output_model=FindAccommodationOutput,
            handler=find_accommodation,
        ),
        ToolSpec(
            name="get_weather",
            description="Get typical weather for a location and month.",
            input_model=GetWeatherInput,
            output_model=GetWeatherOutput,
            handler=get_weather,
        ),
        ToolSpec(
            name="get_elevation_profile",
            description="Get terrain difficulty between two points: elevation gain and difficulty rating.",
            input_model=GetElevationProfileInput,
            output_model=GetElevationProfileOutput,
            handler=get_elevation_profile,
        ),
        ToolSpec(
            name="get_points_of_interest",
            description="Get points of interest near a location (sights, food, bike shops, nature, museums).",
            input_model=PointsOfInterestInput,
            output_model=PointsOfInterestOutput,
            handler=get_points_of_interest,
        ),
        ToolSpec(
            name="check_visa_requirements",
            description="Check visa requirements based on nationality, destination, and stay duration (mock).",
            input_model=VisaRequirementsInput,
            output_model=VisaRequirementsOutput,
            handler=check_visa_requirements,
        ),
        ToolSpec(
            name="estimate_budget",
            description="Estimate trip budget (EUR) given days, daily km, and style preferences (mock).",
            input_model=EstimateBudgetInput,
            output_model=EstimateBudgetOutput,
            handler=estimate_budget,
        ),
    ]
    return ToolRegistry(tools)

