from fastapi import APIRouter

from app.config import settings
from app.schemas.health import HealthResponse

API_VERSION = "0.1.0"

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health", response_model=HealthResponse)
def health_v1() -> HealthResponse:
    """Versioned health endpoint returning typed service metadata.

    This is the foundation anchor for the versioned API surface. Product
    routers are added in later stages as their real implementations land.
    """
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=API_VERSION,
    )
