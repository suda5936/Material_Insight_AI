from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.core.errors import APIError
from app.main import create_app


def test_api_error_handler_returns_stable_payload() -> None:
    app = create_app()
    router = APIRouter()

    @router.get("/raise-api-error")
    async def raise_api_error() -> None:
        raise APIError(
            status_code=422,
            error_code="invalid_schedule_input",
            message="Schedule input is invalid.",
            details={"field": "relationships"},
        )

    app.include_router(router)
    response = TestClient(app).get("/raise-api-error")

    assert response.status_code == 422
    assert response.json() == {
        "error_code": "invalid_schedule_input",
        "message": "Schedule input is invalid.",
        "details": {"field": "relationships"},
    }
