import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import settings
from app.schemas.health import HealthResponse
from app.schemas.transcription import TranscriptionResponse
from app.services.gemini_client import GeminiClient, get_gemini_client
from app.services.visual_speech_model import (
    VisualSpeechError,
    VisualSpeechModel,
    get_visual_speech_model,
)

API_VERSION = "0.1.0"

# Bounded to a short utterance; the iOS client caps recording duration too.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

logger = logging.getLogger("voiceback.transcriptions")

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


@router.post("/transcriptions", response_model=TranscriptionResponse, response_model_exclude_none=True)
async def create_transcription(
    file: UploadFile = File(...),  # noqa: B008
    model: VisualSpeechModel = Depends(get_visual_speech_model),  # noqa: B008
    gemini: GeminiClient = Depends(get_gemini_client),  # noqa: B008
) -> TranscriptionResponse:
    """Return raw Auto-AVSR output plus an optional Gemini proposal.

    The upload is forwarded to the Modal Auto-AVSR function, which removes audio
    and resamples before inference. No microphone/audio path is used here. Gemini
    can propose a correction, but this endpoint never treats it as approval to speak.
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

    logger.info(
        "transcription ok: bytes=%d text=%r frames=%s audio_used=%s secs=%s device=%s",
        len(data),
        result.get("text"),
        result.get("frames"),
        result.get("audio_used"),
        result.get("inference_seconds"),
        result.get("device"),
    )
    interpretation = None
    if gemini.api_key:
        try:
            interpretation = await gemini.interpret(
                original_text=result["text"],
                candidates=(result.get("candidates") or [result["text"]])[:5],
            )
        except Exception as exc:
            logger.exception("gemini interpretation failed")
            raise HTTPException(status_code=502, detail="interpretation backend failed") from exc

    return TranscriptionResponse(**result, interpretation=interpretation)
