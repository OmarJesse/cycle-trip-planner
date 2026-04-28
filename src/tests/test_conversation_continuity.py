from fastapi.testclient import TestClient

from src.api.app import app


def test_conversation_continuity_same_id():
    client = TestClient(app)
    r1 = client.post("/api/v1/chat", json={"message": "First message"})
    cid = r1.json()["conversation_id"]

    r2 = client.post("/api/v1/chat", json={"conversation_id": cid, "message": "Second message"})
    assert r2.status_code == 200
    assert r2.json()["conversation_id"] == cid

