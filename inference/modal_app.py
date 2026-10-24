"""Modal GPU entry point for VoiceBack's official Auto-AVSR adapter."""

from __future__ import annotations

import subprocess
import urllib.request
from pathlib import Path

import modal

from model_adapter import ModelAdapter


APP_NAME = "voiceback-inference"
UPSTREAM_REPO = "https://github.com/mpc001/auto_avsr.git"
DEMO_CHECKPOINT_URL = "gdrive://1r1kx7l9sWnDOCnaFHIGvOtzuhFyFA88_"
DEMO_VIDEO_URL = "https://raw.githubusercontent.com/datascientistabhishek/Lip-Reading-AI-model/main/%F0%9F%91%84%20AI%20Lip%20Reader.mp4"

model_volume = modal.Volume.from_name("voiceback-model-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch",
        "torchvision",
        "torchaudio",
        "pytorch-lightning",
        "sentencepiece",
        "av",
        "opencv-python-headless",
        "scikit-image",
        "mediapipe==0.10.21",
        "gdown",
    )
    .run_commands(f"git clone --depth 1 {UPSTREAM_REPO} /opt/auto_avsr")
    .add_local_file("inference/model_adapter.py", "/root/model_adapter.py", copy=True)
)

app = modal.App(APP_NAME)
_ADAPTER: ModelAdapter | None = None


def _download_once(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    temporary = destination.with_suffix(destination.suffix + ".part")
    if url.startswith("gdrive://"):
        import gdown

        gdown.download(id=url.removeprefix("gdrive://"), output=str(temporary), quiet=False)
    else:
        urllib.request.urlretrieve(url, temporary)
    if not temporary.exists() or temporary.stat().st_size == 0:
        raise RuntimeError(f"download did not produce a file: {url}")
    temporary.replace(destination)


def _audio_stream_count(path: Path) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return len([line for line in result.stdout.splitlines() if line.strip()])


def _prepare_video(root: Path, source: Path, video_only: Path) -> None:
    # Auto-AVSR expects 25 fps; phone capture is typically 30/60 fps, so resample
    # (re-encode, not stream-copy) to the model's frame rate while dropping audio.
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(source), "-an", "-vf", "fps=25",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", str(video_only),
        ],
        check=True,
        capture_output=True,
    )
    if _audio_stream_count(video_only) != 0:
        raise RuntimeError("audio stream remained after audio removal")


def _run_model(video_only: Path, root: Path) -> dict[str, object]:
    global _ADAPTER
    checkpoint = root / "vsr_trlrs2lrs3vox2avsp_base.pth"
    _download_once(DEMO_CHECKPOINT_URL, checkpoint)
    if _ADAPTER is None:
        _ADAPTER = ModelAdapter(checkpoint_path=str(checkpoint), device="cuda", beam_size=10)
    return _ADAPTER.transcribe_video(str(video_only))


@app.function(image=image, gpu="T4", timeout=1800, volumes={"/models": model_volume})
def transcribe_video(video_bytes: bytes) -> dict[str, object]:
    """Run real visual-only Auto-AVSR inference on uploaded video bytes."""

    if not video_bytes:
        raise ValueError("video_bytes must not be empty")
    root = Path("/models")
    source = root / "input.mp4"
    video_only = root / "input_video_only.mp4"
    source.write_bytes(video_bytes)
    _prepare_video(root, source, video_only)
    return _run_model(video_only, root)


@app.function(image=image, gpu="T4", timeout=1800, volumes={"/models": model_volume})
def transcribe_official_demo() -> dict[str, object]:
    """Smoke-test the official Auto-AVSR video-only demo and checkpoint."""

    root = Path("/models")
    source = root / "official_demo_source.mp4"
    video_only = root / "official_demo_video_only.mp4"
    _download_once(DEMO_VIDEO_URL, source)
    _prepare_video(root, source, video_only)
    return _run_model(video_only, root)


@app.local_entrypoint()
def main(demo: bool = False, video: str = "", video2: str = "") -> None:
    print(f"{APP_NAME} is authenticated and configured for T4 execution.")
    if demo:
        print(transcribe_official_demo.remote())
        return
    fixtures = [path for path in (video, video2) if path]
    if not fixtures:
        print("Call transcribe_video.remote(video_bytes) only with a consented video fixture.")
        return
    for path in fixtures:
        data = Path(path).read_bytes()
        print(f"\n=== {path} ({len(data)} bytes) ===")
        print(transcribe_video.remote(data))
