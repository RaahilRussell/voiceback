from fastapi.testclient import TestClient

from app.api import v1
from app.main import app

client = TestClient(app)


def test_clarification_resolves_yes_to_first_candidate() -> None:
    response = client.post(
        "/v1/clarifications",
        json={"candidates": ["I AM A PRO", "I AM A BRO"], "answer": "yes"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "selected_text": "I AM A PRO",
        "needs_follow_up": False,
        "question": None,
    }


def test_speech_requires_explicit_approval() -> None:
    response = client.post(
        "/v1/speech",
        json={"user_id": "approval-test", "text": "hello", "approved": False},
    )
    assert response.status_code == 409


def test_enrollment_requires_consent() -> None:
    response = client.post(
        "/v1/voices/enrollment",
        json={"user_id": "consent-test", "consent": False, "voice_id": "voice"},
    )
    assert response.status_code == 403


def test_approved_speech_returns_cartesia_audio(monkeypatch) -> None:
    async def fake_synthesize(text: str, voice_id: str) -> str:
        assert text == "approved sentence"
        assert voice_id == "voice-test"
        return "YXVkaW8="  # base64("audio")

    monkeypatch.setattr(v1.cartesia, "synthesize_base64", fake_synthesize)
    enrollment = client.post(
        "/v1/voices/enrollment",
        json={"user_id": "speech-test", "consent": True, "voice_id": "voice-test"},
    )
    assert enrollment.status_code == 200
    response = client.post(
        "/v1/speech",
        json={"user_id": "speech-test", "text": "approved sentence", "approved": True},
    )
    assert response.status_code == 200
    assert response.json() == {"audio_base64": "YXVkaW8=", "content_type": "audio/mpeg"}
