"""Modal entry point for VoiceBack's GPU-backed visual inference.

This is the remote execution boundary only. The actual Auto-AVSR checkpoint and
model-specific preprocessing are intentionally added in Stage 01 after the
official repository, license, checkpoint, and input contract are verified.
"""

from __future__ import annotations

import modal


APP_NAME = "voiceback-inference"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install("torch", "torchvision", "torchaudio")
)

app = modal.App(APP_NAME)


@app.function(image=image, gpu="T4", timeout=600)
def transcribe_video(video_bytes: bytes) -> dict[str, object]:
    """Run visual-only inference on a remote GPU.

    Replace this guarded boundary with the verified Auto-AVSR adapter in
    Stage 01. It deliberately refuses to fabricate a transcript.
    """

    if not video_bytes:
        raise ValueError("video_bytes must not be empty")
    raise NotImplementedError("Auto-AVSR integration belongs to Stage 01")


@app.local_entrypoint()
def main() -> None:
    print(f"{APP_NAME} is configured for Modal GPU execution.")
    print("Model weights and real inference are intentionally deferred to Stage 01.")

