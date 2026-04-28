from __future__ import annotations

from fastapi import APIRouter, Depends

from src.agent.runtime import Runtime
from src.api.deps import get_runtime
from src.tools.check_visa_requirements import VisaRequirementsInput, VisaRequirementsOutput
from src.tools.estimate_budget import EstimateBudgetInput, EstimateBudgetOutput
from src.tools.find_accommodation import FindAccommodationInput, FindAccommodationOutput
from src.tools.get_elevation_profile import GetElevationProfileInput, GetElevationProfileOutput
from src.tools.get_points_of_interest import PointsOfInterestInput, PointsOfInterestOutput
from src.tools.get_route import GetRouteInput, GetRouteOutput
from src.tools.get_weather import GetWeatherInput, GetWeatherOutput
from src.tools.names import ToolName


router = APIRouter(prefix="/tools", tags=["v1"])


@router.post("/get_route", response_model=GetRouteOutput)
def route(req: GetRouteInput, rt: Runtime = Depends(get_runtime)) -> GetRouteOutput:
    out = rt.orchestrator_v1.registry.dispatch(ToolName.GET_ROUTE, req.model_dump())
    return GetRouteOutput.model_validate(out)


@router.post("/find_accommodation", response_model=FindAccommodationOutput)
def lodging(req: FindAccommodationInput, rt: Runtime = Depends(get_runtime)) -> FindAccommodationOutput:
    out = rt.orchestrator_v1.registry.dispatch(ToolName.FIND_ACCOMMODATION, req.model_dump())
    return FindAccommodationOutput.model_validate(out)


@router.post("/get_weather", response_model=GetWeatherOutput)
def weather(req: GetWeatherInput, rt: Runtime = Depends(get_runtime)) -> GetWeatherOutput:
    out = rt.orchestrator_v1.registry.dispatch(ToolName.GET_WEATHER, req.model_dump())
    return GetWeatherOutput.model_validate(out)


@router.post("/get_elevation_profile", response_model=GetElevationProfileOutput)
def elevation(req: GetElevationProfileInput, rt: Runtime = Depends(get_runtime)) -> GetElevationProfileOutput:
    out = rt.orchestrator_v1.registry.dispatch(ToolName.GET_ELEVATION_PROFILE, req.model_dump())
    return GetElevationProfileOutput.model_validate(out)


@router.post("/get_points_of_interest", response_model=PointsOfInterestOutput)
def poi(req: PointsOfInterestInput, rt: Runtime = Depends(get_runtime)) -> PointsOfInterestOutput:
    out = rt.orchestrator_v1.registry.dispatch(ToolName.GET_POINTS_OF_INTEREST, req.model_dump())
    return PointsOfInterestOutput.model_validate(out)


@router.post("/check_visa_requirements", response_model=VisaRequirementsOutput)
def visa(req: VisaRequirementsInput, rt: Runtime = Depends(get_runtime)) -> VisaRequirementsOutput:
    out = rt.orchestrator_v1.registry.dispatch(ToolName.CHECK_VISA_REQUIREMENTS, req.model_dump())
    return VisaRequirementsOutput.model_validate(out)


@router.post("/estimate_budget", response_model=EstimateBudgetOutput)
def budget(req: EstimateBudgetInput, rt: Runtime = Depends(get_runtime)) -> EstimateBudgetOutput:
    out = rt.orchestrator_v1.registry.dispatch(ToolName.ESTIMATE_BUDGET, req.model_dump())
    return EstimateBudgetOutput.model_validate(out)
