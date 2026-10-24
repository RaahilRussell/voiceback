from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """Typed visual-only transcription result returned to the iOS client.

    Mirrors the real Auto-AVSR adapter output. `audio_used` must always be
    False: the recognition path is visual-only and the server rejects any
    result claiming an audio path was consumed.
    """

    text: str
    candidates: list[str] = Field(default_factory=list)
    audio_used: bool
    frames: int
    device: str
    inference_seconds: float
    model: str
