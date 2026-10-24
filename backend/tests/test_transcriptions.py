import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.visual_speech_model import VisualSpeechError, get_visual_speech_model

GOOD_RESULT = {
    "text": "THIS IS THE GROUND TRUTH",
    "candidates": ["THIS IS THE GROUND TRUTH"],
    "audio_used": False,
    "frames": 123,
    "device": "cuda:0",
    "inference_seconds": 7.234,
    "model": "mpc001/auto_avsr",
}


class _FakeModel:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def predict(self, video_bytes: bytes) -> dict:
        assert isinstance(video_bytes, bytes) and video_bytes
        if self.error is not None:
            raise self.error
        return self.result


def _client(model: _FakeModel) -> TestClient:
    app.dependency_overrides[get_visual_speech_model] = lambda: model
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_transcription_success_returns_typed_payload():
    client = _client(_FakeModel(result=GOOD_RESULT))
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("clip.mp4", b"\x00\x01\x02fakevideo", "video/mp4")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "THIS IS THE GROUND TRUTH"
    assert body["audio_used"] is False
    assert set(body.keys()) == set(GOOD_RESULT.keys())


def test_rejects_non_video_upload():
    client = _client(_FakeModel(result=GOOD_RESULT))
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415


def test_rejects_empty_video():
    client = _client(_FakeModel(result=GOOD_RESULT))
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("clip.mp4", b"", "video/mp4")},
    )
    assert response.status_code == 400


def test_no_face_maps_to_422():
    client = _client(_FakeModel(error=VisualSpeechError("no detectable face")))
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("clip.mp4", b"\x00\x01", "video/mp4")},
    )
    assert response.status_code == 422
    assert "face" in response.json()["detail"]


def test_provider_failure_maps_to_502():
    client = _client(_FakeModel(error=RuntimeError("modal unreachable")))
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("clip.mp4", b"\x00\x01", "video/mp4")},
    )
    assert response.status_code == 502


def test_audio_used_result_rejected():
    client = _client(_FakeModel(result={**GOOD_RESULT, "audio_used": True}))
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("clip.mp4", b"\x00\x01", "video/mp4")},
    )
    assert response.status_code == 500
