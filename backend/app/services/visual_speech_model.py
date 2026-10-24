"""Visual-only VSR boundary.

Heavy Auto-AVSR inference runs on the Modal T4 app (`inference/modal_app.py`),
which strips audio and resamples to 25 fps before the model ever sees a frame.
This module is the backend's thin boundary to that function; it never consumes
microphone audio. The provider is resolved through a FastAPI dependency so tests
can substitute a fake without touching Modal or a GPU.
"""

from __future__ import annotations

from typing import Protocol

MODAL_APP = "voiceback-inference"
MODAL_FUNCTION = "transcribe_video"


class VisualSpeechError(RuntimeError):
    """Raised when the provider cannot produce a transcript (e.g. no face)."""


class VisualSpeechModel(Protocol):
    def predict(self, video_bytes: bytes) -> dict: ...


class ModalVisualSpeechModel:
    """Calls the deployed Modal visual-only Auto-AVSR function."""

    def predict(self, video_bytes: bytes) -> dict:
        import modal

        function = modal.Function.from_name(MODAL_APP, MODAL_FUNCTION)
        return function.remote(video_bytes)


_default_model: VisualSpeechModel = ModalVisualSpeechModel()


def get_visual_speech_model() -> VisualSpeechModel:
    """FastAPI dependency; overridden in tests with a fake provider."""
    return _default_model
