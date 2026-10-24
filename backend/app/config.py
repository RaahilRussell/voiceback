from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    gemini_api_key: str | None = None
    cartesia_api_key: str | None = None
    cartesia_voice_id: str | None = None
    model_checkpoint_path: str | None = None
    model_device: str = "auto"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VOICEBACK_", extra="ignore")


settings = Settings()

