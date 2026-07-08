from fastapi import APIRouter

from app.models.scan import ScanModelRequest, ScanModelResponse
from app.services.model_scanner import load_default_model_scanner


router = APIRouter(prefix="/api/v1", tags=["scan"])


@router.post("/scan-model", response_model=ScanModelResponse)
def scan_model(request: ScanModelRequest) -> ScanModelResponse:
    scanner = load_default_model_scanner()
    return scanner.scan(request)
