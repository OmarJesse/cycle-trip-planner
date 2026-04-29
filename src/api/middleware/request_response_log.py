from __future__ import annotations

import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.api.middleware.redaction import redact, redact_headers, try_parse_json
from src.logger.logging import get_logger


logger = get_logger("cycling_trip_planner.api")
LOGGED_PATH_PREFIXES = ("/api/",)


class RequestResponseLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, enabled: bool = True, max_log_bytes: int = 40_000):
        super().__init__(app)
        self._enabled = enabled
        self._max_log_bytes = int(max_log_bytes)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._enabled or not _should_log(request.url.path):
            return await call_next(request)

        start = time.time()

        req_body = await request.body()
        request = _rebuild_request(request, req_body)

        resp = await call_next(request)
        resp_body, new_resp = await _capture_response(resp)

        duration_ms = int((time.time() - start) * 1000)
        _log_exchange(request, resp.status_code, duration_ms, req_body, resp_body, self._max_log_bytes)

        return new_resp


def _should_log(path: str) -> bool:
    return any(path.startswith(p) for p in LOGGED_PATH_PREFIXES)


def _rebuild_request(request: Request, body: bytes) -> Request:
    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(request.scope, receive)


async def _capture_response(resp: Response) -> tuple[bytes, Response]:
    body = b""
    async for chunk in resp.body_iterator:
        body += chunk

    new_resp = Response(
        content=body,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.media_type,
    )
    return body, new_resp


def _log_exchange(
    request: Request,
    status_code: int,
    duration_ms: int,
    req_body: bytes,
    resp_body: bytes,
    max_log_bytes: int,
) -> None:
    req_json = try_parse_json(req_body[:max_log_bytes])
    resp_json = try_parse_json(resp_body[:max_log_bytes])
    truncated_resp = len(resp_body) > max_log_bytes
    logger.info(
        "http %s %s -> %s (%sms, %d B%s) headers=%s req=%s resp=%s",
        request.method,
        request.url.path,
        status_code,
        duration_ms,
        len(resp_body),
        " truncated-in-log" if truncated_resp else "",
        redact_headers(request.headers),
        redact(req_json) if req_json is not None else None,
        redact(resp_json) if resp_json is not None else None,
    )
