from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware.rate_limit import RateLimitMiddleware


def test_rate_limit_blocks_after_threshold():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, enabled=True, requests=2, window_seconds=60)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    c = TestClient(app)
    assert c.get("/ping").status_code == 200
    assert c.get("/ping").status_code == 200
    r = c.get("/ping")
    assert r.status_code == 429
    assert "Retry-After" in r.headers

