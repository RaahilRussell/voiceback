from pathlib import Path

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.config import settings
from app.schemas.health import HealthResponse, ReadinessResponse

app = FastAPI(title="VoiceBack API", version="0.1.0")
app.include_router(v1_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=app.version,
    )


@app.get("/readyz", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    reasons: list[str] = []
    checkpoint = Path(settings.model_checkpoint_path) if settings.model_checkpoint_path else None
    generalist_ready = bool(checkpoint and checkpoint.is_file())
    if not generalist_ready:
        reasons.append("model_checkpoint_path is missing or does not point to a local checkpoint")
    gemini_ready = bool(settings.gemini_api_key)
    if not gemini_ready:
        reasons.append("Gemini API key is not configured")
    tts_ready = bool(settings.cartesia_api_key and settings.cartesia_voice_id)
    if not tts_ready:
        reasons.append("Cartesia API key or personal voice ID is not configured")
    return ReadinessResponse(
        generalist_ready=generalist_ready,
        expert_ready=False,
        gemini_ready=gemini_ready,
        tts_ready=tts_ready,
        mode="demo" if settings.demo_mode else "real",
        model_checkpoint=settings.model_checkpoint_path,
        model_device=settings.model_device,
        reasons=reasons,
    )
