import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import DEFAULT_CARTESIA_VOICE_ID, settings
from app.schemas.actions import (
    ClarificationRequest,
    ClarificationResponse,
    SpeechRequest,
    SpeechResponse,
    VoiceEnrollmentRequest,
    VoiceEnrollmentResponse,
)
from app.schemas.health import HealthResponse
from app.schemas.transcription import TranscriptionResponse
from app.services.cartesia_client import CartesiaClient
from app.services.clarification_engine import ClarificationEngine
from app.services.gemini_client import GeminiClient, get_gemini_client
from app.services.visual_speech_model import (
    VisualSpeechError,
    VisualSpeechModel,
    get_visual_speech_model,
)
from app.services.voice_manager import VoiceManager

API_VERSION = "0.1.0"

# Bounded to a short utterance; the iOS client caps recording duration too.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

logger = logging.getLogger("voiceback.transcriptions")
clarification_engine = ClarificationEngine()
voice_manager = VoiceManager()
cartesia = CartesiaClient()

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

    The upload is normalized locally and passed to the configured visual-speech
    backend, which removes audio and resamples before inference. No
    microphone/audio path is used here. Gemini can propose a correction, but
    this endpoint never treats it as approval to speak.
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
        logger.exception("visual speech backend failed")
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
        except Exception as exc:  # noqa: BLE001 - provider outages must not erase raw VSR
            # Gemini is an optional review layer. Never discard a valid visual
            # transcript because the external correction provider is busy or
            # temporarily unavailable; the client will show the raw result and
            # keep speech approval unavailable until review can be completed.
            logger.warning("gemini interpretation unavailable; returning raw transcript: %s", exc)

    return TranscriptionResponse(**result, interpretation=interpretation)


@router.post("/clarifications", response_model=ClarificationResponse)
def resolve_clarification(request: ClarificationRequest) -> ClarificationResponse:
    selected, needs_follow_up = clarification_engine.resolve(request.candidates, request.answer)
    if needs_follow_up:
        return ClarificationResponse(
            selected_text="",
            needs_follow_up=True,
            question=clarification_engine.question_for(request.candidates),
        )
    return ClarificationResponse(selected_text=selected or "", needs_follow_up=False)


@router.post("/voices/enrollment", response_model=VoiceEnrollmentResponse)
def enroll_voice(request: VoiceEnrollmentRequest) -> VoiceEnrollmentResponse:
    try:
        voice_manager.enroll(request.user_id, request.consent, request.voice_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    selected = request.voice_id or settings.cartesia_voice_id or DEFAULT_CARTESIA_VOICE_ID
    return VoiceEnrollmentResponse(
        user_id=request.user_id,
        consented=True,
        voice_id=selected,
        ready=bool(selected and settings.cartesia_api_key),
    )


@router.post("/speech", response_model=SpeechResponse)
async def synthesize_speech(request: SpeechRequest) -> SpeechResponse:
    if not request.approved:
        raise HTTPException(status_code=409, detail="explicit approval is required before speech")
    try:
        voice_id = voice_manager.voice_id(
            request.user_id,
            request.voice_id or settings.cartesia_voice_id or DEFAULT_CARTESIA_VOICE_ID,
        )
        audio = await cartesia.synthesize_base64(request.text, voice_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Cartesia synthesis failed")
        raise HTTPException(status_code=502, detail="speech provider failed") from exc
    return SpeechResponse(audio_base64=audio)
