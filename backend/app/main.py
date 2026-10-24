from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.config import settings
from app.schemas.health import HealthResponse

app = FastAPI(title="VoiceBack API", version="0.1.0")
app.include_router(v1_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=app.version,
    )
