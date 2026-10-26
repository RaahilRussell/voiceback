from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Typed response for service health checks.

    The foundation deliberately exposes only service metadata. Product
    endpoints (transcriptions, clarifications, voices, speech) are planned in
    docs/API_CONTRACT.md and added stage-by-stage, never fabricated here.
    """

    status: str
    environment: str
    version: str


class ReadinessResponse(BaseModel):
    """Explicit capability/readiness report; never implies model readiness."""

    generalist_ready: bool
    expert_ready: bool
    gemini_ready: bool
    tts_ready: bool
    mode: str
    model_checkpoint: str | None
    model_device: str
    reasons: list[str]
