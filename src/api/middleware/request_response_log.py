from __future__ import annotations

import json
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.logger.logging import get_logger

logger = get_logger("cycling_trip_planner.api")


def _try_parse_json(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in {"authorization", "x-api-key", "api_key", "apikey", "anthropic_api_key", "gemini_api_key"}:
                out[k] = "***REDACTED***"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


class RequestResponseLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, enabled: bool = True, max_body_bytes: int = 40_000):
        super().__init__(app)
        self._enabled = enabled
        self._max_body_bytes = int(max_body_bytes)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._enabled:
            return await call_next(request)

        # Only log API routes where request bodies are useful.
        if not (request.url.path.startswith("/api/") or request.url.path == "/chat"):
            return await call_next(request)

        start = time.time()

        req_body = await request.body()
        if len(req_body) > self._max_body_bytes:
            req_body = req_body[: self._max_body_bytes]

        # Re-inject body so downstream can read it
        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": req_body, "more_body": False}

        request = Request(request.scope, receive)

        resp = await call_next(request)

        # Capture response body (non-streaming)
        resp_body = b""
        async for chunk in resp.body_iterator:
            resp_body += chunk
            if len(resp_body) > self._max_body_bytes:
                resp_body = resp_body[: self._max_body_bytes]
                break

        # Rebuild response with captured body
        new_resp = Response(
            content=resp_body,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            media_type=resp.media_type,
        )

        duration_ms = int((time.time() - start) * 1000)

        req_json = _try_parse_json(req_body)
        resp_json = _try_parse_json(resp_body)

        logger.info(
            "http %s %s -> %s (%sms) req=%s resp=%s",
            request.method,
            request.url.path,
            resp.status_code,
            duration_ms,
            _redact(req_json) if req_json is not None else None,
            _redact(resp_json) if resp_json is not None else None,
        )

        return new_resp

