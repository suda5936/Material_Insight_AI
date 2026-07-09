import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analysis import router as analysis_router
from app.api.routes_health import router as health_router
from app.api.routes_knowledge import router as knowledge_router
from app.api.routes_projects import router as projects_router
from app.api.routes_schedule import router as schedule_router
from app.core.config import get_settings
from app.core.errors import APIError, api_error_handler
from app.core.logging import configure_logging

logger = logging.getLogger("app.request")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="P6 Schedule Recovery Copilot Backend",
        version="0.1.0",
        description=(
            "Backend API for deterministic P6 schedule recovery support."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    app.add_exception_handler(APIError, api_error_handler)
    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(schedule_router)
    app.include_router(knowledge_router)
    app.include_router(analysis_router)
    return app


app = create_app()
