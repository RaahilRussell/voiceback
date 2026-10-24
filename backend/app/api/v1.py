from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import settings
from app.schemas.health import HealthResponse
from app.schemas.transcription import TranscriptionResponse
from app.services.visual_speech_model import (
    VisualSpeechError,
    VisualSpeechModel,
    get_visual_speech_model,
)

API_VERSION = "0.1.0"

# Bounded to a short utterance; the iOS client caps recording duration too.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

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


@router.post("/transcriptions", response_model=TranscriptionResponse)
async def create_transcription(
    file: UploadFile = File(...),
    model: VisualSpeechModel = Depends(get_visual_speech_model),
) -> TranscriptionResponse:
    """Accept a video-only upload and return the real visual-only transcript.

    The upload is forwarded to the Modal Auto-AVSR function, which removes audio
    and resamples before inference. No microphone/audio path is used here.
    """
    content_type = file.content_type or ""
    if not content_type.startswith("video/"):
        raise HTTPException(
            status_code=415,
            detail=f"expected a video upload, got '{content_type or 'unknown'}'",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="uploaded video is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="video exceeds the maximum upload size")

    try:
        result = model.predict(data)
    except VisualSpeechError as exc:
        # Recoverable: no detectable face, unintelligible, etc.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # provider/transport failure
        raise HTTPException(status_code=502, detail="visual speech backend failed") from exc

    if result.get("audio_used"):
        raise HTTPException(status_code=500, detail="video-only contract violated: audio_used was true")

    return TranscriptionResponse(**result)
