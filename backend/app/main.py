from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_review import router as review_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Material Insight AI Backend",
        version="0.1.0",
        description=(
            "Backend API for Rhino/CAD object review, rule checking, "
            "retrieval, recommendation, and human review logging."
        ),
    )
    app.include_router(health_router)
    app.include_router(review_router)
    return app


app = create_app()
