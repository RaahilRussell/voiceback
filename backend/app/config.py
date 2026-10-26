from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VOICEBACK_GEMINI_API_KEY", "GEMINI_API_KEY"),
    )
    gemini_model: str = Field(
        default="gemini-3.1-flash-lite",
        validation_alias=AliasChoices("VOICEBACK_GEMINI_MODEL", "GEMINI_MODEL"),
    )
    cartesia_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VOICEBACK_CARTESIA_API_KEY", "CARTESIA_API_KEY"),
    )
    cartesia_voice_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VOICEBACK_CARTESIA_VOICE_ID", "CARTESIA_VOICE_ID"),
    )
    cartesia_model: str = Field(default="sonic-2", validation_alias=AliasChoices("VOICEBACK_CARTESIA_MODEL", "CARTESIA_MODEL"))
    cartesia_version: str = Field(default="2025-04-16", validation_alias=AliasChoices("VOICEBACK_CARTESIA_VERSION", "CARTESIA_VERSION"))
    model_checkpoint_path: str | None = Field(default=None, validation_alias=AliasChoices("VOICEBACK_MODEL_CHECKPOINT_PATH", "MODEL_CHECKPOINT_PATH"))
    model_device: str = Field(default="auto", validation_alias=AliasChoices("VOICEBACK_MODEL_DEVICE", "MODEL_DEVICE"))
    inference_backend: str = Field(default="local", validation_alias=AliasChoices("VOICEBACK_INFERENCE_BACKEND", "INFERENCE_BACKEND"))
    model_upstream_root: str = Field(default="/opt/auto_avsr", validation_alias=AliasChoices("VOICEBACK_MODEL_UPSTREAM_ROOT", "MODEL_UPSTREAM_ROOT"))
    model_beam_size: int = Field(default=5, validation_alias=AliasChoices("VOICEBACK_MODEL_BEAM_SIZE", "MODEL_BEAM_SIZE"))
    demo_mode: bool = Field(default=False, validation_alias=AliasChoices("VOICEBACK_DEMO_MODE", "DEMO_MODE"))
    real_model: bool = Field(default=True, validation_alias=AliasChoices("VOICEBACK_REAL_MODEL", "REAL_MODEL"))
    allow_video_upload: bool = Field(default=True, validation_alias=AliasChoices("VOICEBACK_ALLOW_VIDEO_UPLOAD", "ALLOW_VIDEO_UPLOAD"))
    backend_url: str = Field(default="http://127.0.0.1:8000", validation_alias=AliasChoices("VOICEBACK_BACKEND_URL", "BACKEND_URL"))

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VOICEBACK_", extra="ignore")


settings = Settings()

# Public Cartesia demo voice used only when a personal consented voice has not
# been configured yet. A user-provided voice ID always overrides this value.
DEFAULT_CARTESIA_VOICE_ID = "694f9389-aac1-45b6-b726-9d9369183238"

