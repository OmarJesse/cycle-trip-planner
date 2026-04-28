from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v0.chat import router as v0_router
from src.api.v1.chat import router as v1_router
from src.api.v1.dependencies import get_runtime


def create_app() -> FastAPI:
    rt = get_runtime()
    app = FastAPI(title=rt.settings.api_title, version=rt.settings.api_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=rt.settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(v0_router)
    app.include_router(v1_router)
    # Convenience alias (v1)
    from src.api.v1.chat import chat as v1_chat  # import here to avoid circulars

    app.add_api_route("/chat", endpoint=v1_chat, methods=["POST"])
    return app


app = create_app()

