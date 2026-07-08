from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_actions import router as actions_router
from app.api.routes_health import router as health_router
from app.api.routes_review import router as review_router
from app.api.routes_scan import router as scan_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Material Insight AI Backend",
        version="0.1.0",
        description=(
            "Backend API for Rhino/CAD object review, rule checking, "
            "retrieval, recommendation, and human review logging."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(review_router)
    app.include_router(actions_router)
    app.include_router(scan_router)
    return app


app = create_app()
