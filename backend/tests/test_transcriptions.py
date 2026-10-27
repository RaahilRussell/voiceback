import pytest
from fastapi.testclient import TestClient

from app.api import v1 as v1_api
from app.main import app
from app.schemas.interpretation import InterpretationResult
from app.services.gemini_client import get_gemini_client
from app.services.visual_speech_model import VisualSpeechError, get_visual_speech_model

GOOD_RESULT = {
    "text": "THIS IS THE GROUND TRUTH",
    "candidates": ["THIS IS THE GROUND TRUTH", "THIS IS THE GROUND TRUCE"],
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

    def predict(self, video_bytes: bytes, developer_mode: bool = False) -> dict:
        assert isinstance(video_bytes, bytes) and video_bytes
        if self.error is not None:
            raise self.error
        return self.result


class _FakeGemini:
    def __init__(self, result: InterpretationResult | None = None):
        self.api_key = "test-key" if result else None
        self.result = result

    async def interpret(self, original_text: str, candidates: list[str]) -> InterpretationResult:
        assert original_text == GOOD_RESULT["text"]
        assert candidates == GOOD_RESULT["candidates"]
        assert self.result is not None
        return self.result


class _UnavailableGemini:
    api_key = "test-key"

    async def interpret(self, original_text: str, candidates: list[str]) -> InterpretationResult:
        raise RuntimeError("provider temporarily unavailable")


def _client(model: _FakeModel, gemini: _FakeGemini | None = None) -> TestClient:
    app.dependency_overrides[get_visual_speech_model] = lambda: model
    app.dependency_overrides[get_gemini_client] = lambda: gemini or _FakeGemini()
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
    assert set(GOOD_RESULT.keys()).issubset(body.keys())
    assert body["developer_diagnostics"]["enabled"] is True


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


def test_configured_gemini_result_is_attached_after_raw_transcript():
    interpretation = InterpretationResult(
        original_text=GOOD_RESULT["text"],
        corrected_text=GOOD_RESULT["text"],
        candidates=GOOD_RESULT["candidates"],
        selected_index=0,
        confidence=0.96,
        needs_clarification=False,
    )
    client = _client(_FakeModel(result=GOOD_RESULT), _FakeGemini(interpretation))
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("clip.mp4", b"\x00\x01\x02fakevideo", "video/mp4")},
    )
    assert response.status_code == 200
    assert response.json()["interpretation"]["corrected_text"] == GOOD_RESULT["text"]


def test_gemini_outage_preserves_raw_transcript_without_approval():
    client = _client(_FakeModel(result=GOOD_RESULT), _UnavailableGemini())
    response = client.post(
        "/v1/transcriptions",
        files={"file": ("clip.mp4", b"\x00\x01\x02fakevideo", "video/mp4")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == GOOD_RESULT["text"]
    assert body["audio_used"] is False
    assert "interpretation" not in body


def test_stream_session_emits_bounded_events_and_final_candidates(monkeypatch):
    model = _FakeModel(result=GOOD_RESULT)
    interpretation = InterpretationResult(
        original_text=GOOD_RESULT["text"],
        corrected_text=GOOD_RESULT["text"],
        candidates=GOOD_RESULT["candidates"],
        selected_index=0,
        confidence=0.96,
        needs_clarification=False,
    )
    monkeypatch.setattr(v1_api, "get_visual_speech_model", lambda: model)
    monkeypatch.setattr(v1_api.StreamingSession, "_encode_video", lambda self, frames=None: b"video")
    monkeypatch.setattr(v1_api, "get_gemini_client", lambda: _FakeGemini(interpretation))

    with TestClient(app).websocket_connect("/v1/sessions/client-session/stream") as socket:
        ready = socket.receive_json()
        assert ready["event"] == "session_ready"
        assert ready["capabilities"]["model_streaming"] is False
        socket.send_json({"type": "start", "fps": 25})
        negotiated = socket.receive_json()
        assert negotiated["event"] == "session_ready"
        assert negotiated["capabilities"]["partial_hypotheses"] is False
        assert socket.receive_json()["event"] == "utterance_started"
        socket.send_bytes(b"jpeg-frame")
        quality = socket.receive_json()
        assert quality["event"] == "capture_quality"
        assert quality["frame_count"] == 1
        socket.send_json({"type": "end"})
        partial = socket.receive_json()
        final = socket.receive_json()
        assert partial["event"] == "partial_hypothesis"
        assert partial["generation_mode"] == "offline_final_decode"
        assert final["event"] == "final_candidates"
        assert final["text"] == GOOD_RESULT["text"]
        context = socket.receive_json()
        decision = socket.receive_json()
        assert context["event"] == "context_result"
        assert context["interpretation"]["corrected_text"] == GOOD_RESULT["text"]
        assert decision["event"] == "decision"
        assert decision["decision"] == "awaiting_approval"
