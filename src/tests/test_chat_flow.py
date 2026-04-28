from fastapi.testclient import TestClient

from src.api.app import app


def test_chat_returns_conversation_id_and_reply():
    client = TestClient(app)
    resp = client.post("/chat", json={"message": "I want to cycle from Amsterdam to Copenhagen. Traveling in June."})
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data and data["conversation_id"]
    assert "reply" in data and data["reply"]


def test_v0_and_v1_routes_exist():
    client = TestClient(app)
    r0 = client.post("/api/v0/chat", json={"message": "Hello"})
    assert r0.status_code == 200
    r1 = client.post("/api/v1/chat", json={"message": "Hello"})
    assert r1.status_code == 200

