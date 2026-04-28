from __future__ import annotations

import time
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class _Window:
    start: float
    count: int


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        requests: int,
        window_seconds: int,
        enabled: bool = True,
    ):
        super().__init__(app)
        self._enabled = enabled
        self._requests = int(requests)
        self._window_seconds = int(window_seconds)
        self._by_key: dict[str, _Window] = {}

    def _key(self, request: Request) -> str:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            ip = fwd.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return ip

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._enabled:
            return await call_next(request)

        key = self._key(request)
        now = time.time()
        w = self._by_key.get(key)
        if w is None or (now - w.start) >= self._window_seconds:
            w = _Window(start=now, count=0)
            self._by_key[key] = w

        w.count += 1
        if w.count > self._requests:
            retry_after = max(0, int(self._window_seconds - (now - w.start)))
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited"},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)

