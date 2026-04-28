from fastapi.testclient import TestClient

from src.api.app import app


def test_chat_returns_conversation_id_and_reply():
    client = TestClient(app)
    resp = client.post("/api/v1/chat", json={"message": "I want to cycle from Amsterdam to Copenhagen. Traveling in June."})
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data and data["conversation_id"]
    assert "reply" in data and data["reply"]


def test_v0_and_v1_routes_exist():
    client = TestClient(app)
    r0 = client.post("/api/v0/chat", json={"message": "Hello"})
    assert r0.status_code == 200
    assert "Tell me" in r0.json()["reply"]
    r1 = client.post("/api/v1/chat", json={"message": "Hello"})
    assert r1.status_code == 200


def test_v0_optional_tools_routes_exist():
    client = TestClient(app)
    r = client.post("/api/v0/tools/get_points_of_interest", json={"near": "Copenhagen", "category": "any", "limit": 3})
    assert r.status_code == 200

