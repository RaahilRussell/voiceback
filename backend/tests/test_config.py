import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.environment == "development"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    # Provider secrets must be absent by default; they are supplied via env.
    assert settings.gemini_api_key is None
    assert settings.cartesia_api_key is None


def test_settings_rejects_invalid_port() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, port="not-a-number")
