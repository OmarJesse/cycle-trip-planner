from src.tools.check_visa_requirements import VisaRequirementsInput, check_visa_requirements
from src.tools.estimate_budget import EstimateBudgetInput, estimate_budget
from src.tools.get_points_of_interest import PointsOfInterestInput, get_points_of_interest


def test_points_of_interest_limit():
    out = get_points_of_interest(PointsOfInterestInput(near="Hamburg", category="any", limit=5))
    assert out.near == "Hamburg"
    assert len(out.items) == 5


def test_visa_requirements_shape():
    out = check_visa_requirements(VisaRequirementsInput(nationality="Canadian", destination_country="Denmark", stay_days=14))
    assert out.destination_country == "Denmark"
    assert out.requirement in ("unknown", "likely_not_required", "may_be_required")


def test_budget_estimate_positive():
    out = estimate_budget(EstimateBudgetInput(days=7, daily_distance_km=100, lodging_style="mixed", food_style="balanced"))
    assert out.estimated_total > 0
    assert out.currency == "EUR"

