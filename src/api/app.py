from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.health import router as health_router
from src.api.middleware.rate_limit import RateLimitMiddleware
from src.api.middleware.request_response_log import RequestResponseLogMiddleware
from src.api.v0 import router as v0_router
from src.api.v1 import router as v1_router
from src.api.deps import get_runtime
from src.config.version import get_version


def create_app() -> FastAPI:
    rt = get_runtime()
    app = FastAPI(title=rt.settings.api_title, version=get_version())

    app.add_middleware(RequestResponseLogMiddleware, enabled=True)
    app.add_middleware(
        RateLimitMiddleware,
        enabled=rt.settings.rate_limit_enabled,
        requests=rt.settings.rate_limit_requests,
        window_seconds=rt.settings.rate_limit_window_seconds,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=rt.settings.cors_allow_origins,
        allow_credentials=False,
        allow_methods=rt.settings.cors_allow_methods,
        allow_headers=rt.settings.cors_allow_headers,
    )

    app.include_router(health_router)
    app.include_router(v0_router)
    app.include_router(v1_router)

    return app


app = create_app()
