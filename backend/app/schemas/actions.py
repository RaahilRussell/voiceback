from pydantic import BaseModel, Field


class ClarificationRequest(BaseModel):
    candidates: list[str] = Field(min_length=2, max_length=5)
    answer: str = Field(min_length=1, max_length=32)


class ClarificationResponse(BaseModel):
    selected_text: str
    needs_follow_up: bool
    question: str | None = None


class VoiceEnrollmentRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    consent: bool
    voice_id: str | None = Field(default=None, min_length=1, max_length=256)


class VoiceEnrollmentResponse(BaseModel):
    user_id: str
    consented: bool
    voice_id: str | None
    ready: bool


class SpeechRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=1000)
    approved: bool
    voice_id: str | None = Field(default=None, min_length=1, max_length=256)


class SpeechResponse(BaseModel):
    audio_base64: str
    content_type: str = "audio/mpeg"
