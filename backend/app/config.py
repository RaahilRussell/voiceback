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
    model_checkpoint_path: str | None = None
    model_device: str = "auto"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VOICEBACK_", extra="ignore")


settings = Settings()

# Public Cartesia demo voice used only when a personal consented voice has not
# been configured yet. A user-provided voice ID always overrides this value.
DEFAULT_CARTESIA_VOICE_ID = "694f9389-aac1-45b6-b726-9d9369183238"

