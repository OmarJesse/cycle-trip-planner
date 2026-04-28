from src.tools.get_route import GetRouteInput, get_route


def test_get_route_shape():
    out = get_route(GetRouteInput(origin="Amsterdam", destination="Copenhagen"))
    assert out.total_distance_km > 0
    assert out.origin == "Amsterdam"
    assert out.destination == "Copenhagen"
    assert len(out.waypoints) >= 2

