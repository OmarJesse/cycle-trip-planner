from __future__ import annotations

from fastapi.testclient import TestClient


def test_v0_tools_route_and_weather() -> None:
    from src.api.app import create_app

    client = TestClient(create_app())

    r = client.post("/api/v0/tools/get_route", json={"origin": "Ams", "destination": "Bru", "days": 3})
    assert r.status_code == 200
    data = r.json()
    assert "total_distance_km" in data
    assert data["origin"] == "Ams"
    assert data["destination"] == "Bru"

    w = client.post("/api/v0/tools/get_weather", json={"location": "Ams", "month": "June"})
    assert w.status_code == 200
    wdata = w.json()
    assert wdata["location"] == "Ams"
    assert wdata["month"] == "June"

