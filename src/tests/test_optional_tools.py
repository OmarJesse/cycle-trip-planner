import pytest
from pydantic import ValidationError

from src.config.runtime import get_settings
from src.tools.check_visa_requirements import VisaRequirementsInput, check_visa_requirements
from src.tools.estimate_budget import EstimateBudgetInput, estimate_budget
from src.tools.get_points_of_interest import PointsOfInterestInput, get_points_of_interest


def test_points_of_interest_respects_explicit_limit():
    out = get_points_of_interest(PointsOfInterestInput(near="Hamburg", category="any", limit=5))
    assert out.near == "Hamburg"
    assert len(out.items) == 5
    assert all(item.category == out.category for item in out.items)


def test_points_of_interest_default_limit_falls_back_to_settings():
    settings = get_settings()
    out = get_points_of_interest(PointsOfInterestInput(near="Bremen"))
    assert len(out.items) == settings.mock_poi_default_limit


def test_points_of_interest_schema_exposes_limit_with_no_runtime_factory():
    schema = PointsOfInterestInput.model_json_schema()
    assert "limit" in schema["properties"]
    limit_schema = schema["properties"]["limit"]
    assert limit_schema.get("default", "MISSING") in (None, "MISSING") or limit_schema["default"] is None
    assert "limit" not in schema.get("required", [])


def test_points_of_interest_specific_category_overrides_random_pick():
    out = get_points_of_interest(PointsOfInterestInput(near="Utrecht", category="bike_shops", limit=3))
    assert out.category == "bike_shops"
    assert all(item.category == "bike_shops" for item in out.items)


def test_visa_requirement_likely_not_required_for_short_schengen_stay():
    out = check_visa_requirements(VisaRequirementsInput(
        nationality="Canadian", destination_country="Denmark", stay_days=14
    ))
    assert out.requirement == "likely_not_required"


def test_visa_requirement_may_be_required_when_stay_exceeds_threshold():
    settings = get_settings()
    out = check_visa_requirements(VisaRequirementsInput(
        nationality="Canadian",
        destination_country="Denmark",
        stay_days=settings.mock_visa_max_days_no_visa + 1,
    ))
    assert out.requirement == "may_be_required"


def test_visa_requirement_may_be_required_outside_schengen():
    out = check_visa_requirements(VisaRequirementsInput(
        nationality="Canadian", destination_country="Russia", stay_days=10
    ))
    assert out.requirement == "may_be_required"


def test_visa_input_rejects_too_short_nationality():
    with pytest.raises(ValidationError):
        VisaRequirementsInput(nationality="C", destination_country="Denmark", stay_days=10)


def test_budget_total_matches_breakdown_times_days():
    out = estimate_budget(EstimateBudgetInput(
        days=7, daily_distance_km=100, lodging_style="camping", food_style="budget"
    ))
    expected = sum(out.breakdown_per_day.values()) * out.days
    assert out.estimated_total == expected
    assert out.currency == "EUR"


def test_budget_uses_rounded_total_not_truncation():
    # Force a fractional km that makes the variable component non-integer before summing.
    settings = get_settings()
    inp = EstimateBudgetInput(days=3, daily_distance_km=125, lodging_style="hostel", food_style="treats")
    out = estimate_budget(inp)
    # estimated_total must equal int(round(per_day_sum * days))
    assert out.estimated_total == int(round(sum(out.breakdown_per_day.values()) * out.days))
    # Treats should cost more than budget for the same trip.
    cheaper = estimate_budget(inp.model_copy(update={"food_style": "budget"}))
    assert out.estimated_total > cheaper.estimated_total
    assert out.breakdown_per_day["lodging"] == settings.mock_budget_lodging_hostel


def test_budget_scales_linearly_with_days():
    base = estimate_budget(EstimateBudgetInput(
        days=2, daily_distance_km=80, lodging_style="mixed", food_style="balanced"
    ))
    longer = estimate_budget(EstimateBudgetInput(
        days=4, daily_distance_km=80, lodging_style="mixed", food_style="balanced"
    ))
    assert longer.estimated_total == 2 * base.estimated_total
