"""Video normalization helpers shared by local and remote inference."""

import subprocess
from pathlib import Path


def normalize_video(input_path: str, output_path: str) -> str:
    source = Path(input_path)
    destination = Path(output_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(source), "-an", "-vf", "fps=25",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", str(destination),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return str(destination)

