from fastapi import APIRouter

from config.settings import settings
from library.base.api_response import ApiResponse

from .system_vo import HealthVO

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health", response_model=ApiResponse[HealthVO])
def health_check():
    return ApiResponse.success(
        data=HealthVO(status="ok", version=settings.app_version)
    )
