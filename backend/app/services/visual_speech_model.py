"""Visual-only VSR boundary with local laptop inference as the default."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Protocol

from app.config import settings

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


class LocalVisualSpeechModel:
    """Warm, in-process Auto-AVSR adapter for the developer laptop."""

    def __init__(self) -> None:
        self._adapter = None

    def predict(self, video_bytes: bytes) -> dict:
        if not settings.real_model:
            raise VisualSpeechError("REAL_MODEL=false; synthetic recognition is not enabled")
        if not settings.model_checkpoint_path:
            raise VisualSpeechError(
                "local model is not ready: set MODEL_CHECKPOINT_PATH to an authorized Auto-AVSR checkpoint"
            )
        repository_root = Path(__file__).resolve().parents[3]
        if str(repository_root) not in sys.path:
            sys.path.insert(0, str(repository_root))
        from inference.model_adapter import ModelAdapter

        if self._adapter is None:
            self._adapter = ModelAdapter(
                checkpoint_path=settings.model_checkpoint_path,
                device=settings.model_device,
                upstream_root=settings.model_upstream_root,
                beam_size=settings.model_beam_size,
                lm_model_name=settings.lm_model_name,
                lm_fusion_weight=settings.lm_fusion_weight,
            )
        with tempfile.TemporaryDirectory(prefix="voiceback-local-") as directory:
            source = f"{directory}/source.mov"
            normalized = f"{directory}/video-only.mp4"
            with open(source, "wb") as handle:
                handle.write(video_bytes)
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", source, "-an", "-vf", "fps=25", "-c:v", "libx264", "-preset", "ultrafast", normalized],
                    check=True,
                    capture_output=True,
                )
                return self._adapter.transcribe_video(normalized)
            except FileNotFoundError as exc:
                raise VisualSpeechError("ffmpeg is required for local visual-only inference") from exc
            except subprocess.CalledProcessError as exc:
                raise VisualSpeechError("local video normalization failed") from exc
            except (ImportError, RuntimeError, ValueError) as exc:
                raise VisualSpeechError(f"local Auto-AVSR inference failed: {exc}") from exc


_local_model: VisualSpeechModel = LocalVisualSpeechModel()
_modal_model: VisualSpeechModel = ModalVisualSpeechModel()


def get_visual_speech_model() -> VisualSpeechModel:
    """FastAPI dependency; tests override this without touching a runtime."""
    if settings.inference_backend == "modal":
        return _modal_model
    return _local_model
