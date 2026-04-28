from src.tools.get_elevation_profile import GetElevationProfileInput, get_elevation_profile


def test_get_elevation_profile_difficulty():
    out = get_elevation_profile(GetElevationProfileInput(origin="AA", destination="BB", distance_km=100))
    assert out.elevation_gain_m > 0
    assert out.difficulty in ("easy", "moderate", "hard")

