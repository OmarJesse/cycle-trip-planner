from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.app import app
from src.api.middleware.request_id import REQUEST_ID_HEADER


def test_response_includes_server_generated_request_id_when_client_omits_header():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    rid = resp.headers.get(REQUEST_ID_HEADER)
    assert rid
    assert len(rid) >= 16


def test_response_echoes_client_supplied_request_id():
    client = TestClient(app)
    resp = client.get("/health", headers={REQUEST_ID_HEADER: "rid-from-caller-123"})
    assert resp.status_code == 200
    assert resp.headers.get(REQUEST_ID_HEADER) == "rid-from-caller-123"


def test_distinct_requests_get_distinct_server_generated_ids():
    client = TestClient(app)
    a = client.get("/health").headers.get(REQUEST_ID_HEADER)
    b = client.get("/health").headers.get(REQUEST_ID_HEADER)
    assert a and b and a != b
