from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_rhino_sync import router as rhino_sync_router
from app.core.config import get_settings
from app.core.errors import APIError, api_error_handler


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="P6 Schedule Recovery Copilot Backend",
        version="0.1.0",
        description=(
            "Backend API for deterministic P6 schedule recovery support. "
            "Rhino object sync is preserved as optional issue-location context."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_exception_handler(APIError, api_error_handler)
    app.include_router(health_router)
    app.include_router(rhino_sync_router)
    return app


app = create_app()
