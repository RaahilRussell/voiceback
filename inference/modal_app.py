"""Modal GPU entry point for VoiceBack's official Auto-AVSR adapter."""

import ast
import base64
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

import modal

from model_adapter import ModelAdapter


APP_NAME = "voiceback-inference"
DEFAULT_CARTESIA_VOICE_ID = "694f9389-aac1-45b6-b726-9d9369183238"
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
        # Beam 5 preserves the official decoder path while avoiding the extra
        # search work of the demo's beam-10 setting. Increase via env only if
        # an evaluation clip shows a measurable accuracy regression.
        beam_size = int(os.getenv("VOICEBACK_BEAM_SIZE", "5"))
        _ADAPTER = ModelAdapter(checkpoint_path=str(checkpoint), device="cuda", beam_size=beam_size)
    return _ADAPTER.transcribe_video(str(video_only))


@app.function(
    image=image,
    gpu="L4",
    timeout=1800,
    min_containers=1,
    scaledown_window=900,
    volumes={"/models": model_volume},
)
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


web_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi[standard]")
    .pip_install("google-genai>=1.0")
    .add_local_file("inference/model_adapter.py", "/root/model_adapter.py", copy=True)
)


# A single Auto-AVSR candidate does not need a second network round-trip unless
# it contains a known lip-reading collision.  This keeps ordinary utterances
# on the fast path while preserving Gemini review for cases such as PRO/BRO.
_AMBIGUOUS_WORD_GROUPS = (
    frozenset({"pro", "bro"}),
    frozenset({"me", "be", "pea"}),
    frozenset({"my", "by", "pie"}),
    frozenset({"may", "bay", "pay"}),
    frozenset({"more", "bore", "pour"}),
    frozenset({"map", "nap"}),
    frozenset({"mat", "bat", "pat"}),
    frozenset({"bad", "pad"}),
    frozenset({"bin", "pin"}),
    frozenset({"bit", "pit"}),
    frozenset({"buy", "by", "pie"}),
    frozenset({"mob", "mop"}),
    frozenset({"ram", "rap"}),
    frozenset({"pat", "bat"}),
    frozenset({"park", "bark"}),
    frozenset({"pan", "ban"}),
    frozenset({"pie", "buy"}),
    frozenset({"fan", "van"}),
    frozenset({"fine", "vine"}),
    frozenset({"few", "view"}),
    frozenset({"ferry", "very"}),
    frozenset({"fear", "veer"}),
    frozenset({"fast", "vast"}),
    frozenset({"fane", "vain"}),
    frozenset({"van", "fan"}),
    frozenset({"two", "do"}),
    frozenset({"to", "do"}),
    frozenset({"tin", "din"}),
    frozenset({"ten", "den"}),
    frozenset({"tie", "die"}),
    frozenset({"night", "might"}),
    frozenset({"need", "knead"}),
    frozenset({"no", "know"}),
    frozenset({"not", "knot"}),
    frozenset({"meet", "neat"}),
)


def _requires_gemini(result: dict[str, object]) -> bool:
    """Return whether interpretation can improve the raw VSR result."""

    if os.getenv("VOICEBACK_GEMINI_ALWAYS", "0").lower() in {"1", "true", "yes"}:
        return True
    candidates = list(dict.fromkeys(str(item).strip() for item in (result.get("candidates") or []) if str(item).strip()))
    if len(candidates) != 1:
        return True
    words = {word.lower() for word in re.findall(r"[A-Za-z]+", candidates[0])}
    return any(words.intersection(group) for group in _AMBIGUOUS_WORD_GROUPS)


def _deterministic_interpretation(result: dict[str, object]) -> dict[str, object]:
    """Build the safe no-LLM result for an unambiguous single candidate."""

    text = str(result.get("text") or "").strip()
    candidates = [text]
    return {
        "original_text": text,
        "corrected_text": text,
        "candidates": candidates,
        "selected_index": 0,
        "confidence": 0.90,
        "needs_clarification": False,
        "clarification_question": None,
        # No invented per-word probabilities on the fast path. Word checks are
        # reserved for actual candidate collisions reviewed by Gemini.
        "word_checks": [],
    }


def _interpret_with_gemini(result: dict[str, object]) -> dict[str, object] | None:
    """Add the same guarded interpretation used by the local API."""

    api_key = os.getenv("VOICEBACK_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    from google import genai
    from google.genai import types

    candidates = list(dict.fromkeys(str(item).strip() for item in (result.get("candidates") or []) if str(item).strip()))[:5]
    if not candidates:
        candidates = [str(result.get("text") or "")]
    prompt = (
        "You are a conservative visual-speech verifier. Return exactly one JSON decision. "
        "Choose only among the supplied candidate sentences; never invent, rewrite, or "
        "combine words. Do not treat confidence as a calibrated probability. Only add a "
        "word_check when the word is present in the supplied text and the alternative is a "
        "plausible lip-motion collision such as PRO/BRO, B/P, M/N, or F/V. Never create "
        "checks for ordinary unambiguous words. Set needs_clarification true for genuine "
        "candidate disagreement or an uncertain collision. Ask one short yes/no question "
        "when clarification is needed. Do not authorize speech.\n\n"
        f"Original visual transcription: {result.get('text', '')}\n"
        f"Candidates (JSON): {json.dumps(candidates, ensure_ascii=False)}"
    )
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "original_text": {"type": "STRING"},
            "corrected_text": {"type": "STRING"},
            "candidates": {"type": "ARRAY", "items": {"type": "STRING"}},
            "selected_index": {"type": "INTEGER"},
            "confidence": {"type": "NUMBER"},
            "needs_clarification": {"type": "BOOLEAN"},
            "clarification_question": {"type": "STRING", "nullable": True},
            "word_checks": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "observed_word": {"type": "STRING"},
                        "alternatives": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "confidence": {"type": "NUMBER"},
                        "needs_clarification": {"type": "BOOLEAN"},
                    },
                    "required": ["observed_word", "alternatives", "confidence", "needs_clarification"],
                },
            },
        },
        "required": [
            "original_text", "corrected_text", "candidates", "selected_index",
            "confidence", "needs_clarification", "clarification_question", "word_checks",
        ],
    }
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=30_000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    response = client.models.generate_content(
        model=os.getenv("VOICEBACK_GEMINI_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.0,
            top_p=0.1,
            candidate_count=1,
            max_output_tokens=512,
            seed=7,
        ),
    )
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, dict):
        interpretation = parsed
    elif parsed is not None and hasattr(parsed, "model_dump"):
        interpretation = parsed.model_dump()
    else:
        candidates_response = getattr(response, "candidates", None) or []
        parts = getattr(getattr(candidates_response[0], "content", None), "parts", None) or []
        raw = str(getattr(parts[0], "text", "")).strip() if parts else ""
        if not raw:
            raise ValueError("Gemini returned no candidate text")
        if raw.startswith("```"):
            raw = raw.strip("`").removeprefix("json").strip()
        try:
            interpretation = json.loads(raw)
        except json.JSONDecodeError:
            # Some SDK/container combinations stringify the structured object
            # with single quotes; literal_eval keeps this fallback non-executable.
            interpretation = ast.literal_eval(raw)
        if not isinstance(interpretation, dict):
            raise ValueError("Gemini returned a non-object interpretation")
    return _sanitize_interpretation(interpretation, str(result.get("text") or ""), candidates)


_SAFE_VISUAL_CONFUSION_GROUPS = (
    frozenset({"pro", "bro"}), frozenset({"pat", "bat"}),
    frozenset({"map", "nap"}), frozenset({"fan", "van"}),
    frozenset({"fine", "vine"}), frozenset({"two", "do"}),
    frozenset({"to", "do"}), frozenset({"tin", "din"}),
    frozenset({"ten", "den"}), frozenset({"meet", "neat"}),
)


def _sanitize_interpretation(
    interpretation: dict[str, object], original_text: str, supplied_candidates: list[str]
) -> dict[str, object]:
    """Constrain Gemini to the VSR evidence before it reaches the approval UI."""
    supplied = list(dict.fromkeys(item.strip() for item in supplied_candidates if item.strip()))[:5]
    if not supplied:
        supplied = [original_text.strip()]
    normalized = {item.casefold(): item for item in supplied}
    proposed = str(interpretation.get("corrected_text") or "").strip()
    selected = normalized.get(proposed.casefold(), supplied[0])
    invalid_proposal = proposed.casefold() not in normalized
    source_words = {word.casefold() for word in re.findall(r"[A-Za-z']+", original_text)}
    safe_checks: list[dict[str, object]] = []
    for raw_check in interpretation.get("word_checks", []) or []:
        if not isinstance(raw_check, dict):
            continue
        observed = str(raw_check.get("observed_word") or "").strip()
        alternatives = [str(item).strip() for item in raw_check.get("alternatives", []) or [] if str(item).strip()]
        plausible = any(
            frozenset({observed.casefold(), alternative.casefold()}) <= group
            for group in _SAFE_VISUAL_CONFUSION_GROUPS
            for alternative in alternatives
        )
        if not observed or observed.casefold() not in source_words or not plausible:
            continue
        safe_checks.append({
            "observed_word": observed,
            "alternatives": alternatives[:4],
            "confidence": max(0.0, min(1.0, float(raw_check.get("confidence", 0.0)))),
            "needs_clarification": bool(raw_check.get("needs_clarification")),
        })
    uncertain = [
        check for check in safe_checks
        if check["needs_clarification"] or float(check["confidence"]) < 0.80
    ]
    needs_clarification = bool(interpretation.get("needs_clarification")) or invalid_proposal or bool(uncertain)
    question = interpretation.get("clarification_question")
    if needs_clarification and not question:
        if uncertain:
            check = uncertain[0]
            question = f"Did you mean {check['observed_word']} or {check['alternatives'][0]}?"
        elif len(supplied) > 1:
            question = f"Did you mean {supplied[0]} or {supplied[1]}?"
    if not needs_clarification:
        question = None
    return {
        "original_text": original_text,
        "corrected_text": selected,
        "candidates": supplied,
        "selected_index": supplied.index(selected),
        "confidence": max(0.0, min(1.0, float(interpretation.get("confidence", 0.0)))),
        "needs_clarification": needs_clarification,
        "clarification_question": question,
        "word_checks": safe_checks,
    }


@app.function(image=web_image, secrets=[modal.Secret.from_name("voiceback-secrets")])
@modal.asgi_app()
def web():
    """Public HTTPS endpoint so a phone on any network can reach the VSR path.

    Mirrors the local FastAPI `/v1/transcriptions` contract and forwards the
    upload to the T4 `transcribe_video` function. Audio is stripped inside that
    function; this endpoint never consumes microphone audio.
    """
    from fastapi import FastAPI, File, HTTPException

    api = FastAPI(title="VoiceBack public endpoint")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/v1/transcriptions")
    async def create_transcription(file: Any = File(...)) -> dict:
        content_type = file.content_type or ""
        if not content_type.startswith("video/"):
            raise HTTPException(status_code=415, detail=f"expected a video upload, got '{content_type or 'unknown'}'")
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="uploaded video is empty")
        try:
            result = await transcribe_video.remote.aio(data)
        except Exception as exc:  # GPU/transport failure
            raise HTTPException(status_code=502, detail=f"visual speech backend failed: {exc}") from exc
        if result.get("audio_used"):
            raise HTTPException(status_code=500, detail="video-only contract violated: audio_used was true")
        if not _requires_gemini(result):
            result["interpretation"] = _deterministic_interpretation(result)
            result["interpretation_mode"] = "deterministic_fast_path"
            return result
        try:
            interpretation = _interpret_with_gemini(result)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Gemini interpretation failed: {exc}") from exc
        if interpretation is not None:
            result["interpretation"] = interpretation
        return result

    @api.post("/v1/clarifications")
    async def create_clarification(payload: dict[str, Any]) -> dict[str, Any]:
        candidates = [str(item).strip() for item in payload.get("candidates", []) if str(item).strip()]
        answer = str(payload.get("answer", "")).strip().lower()
        if len(candidates) < 2:
            raise HTTPException(status_code=422, detail="at least two candidates are required")
        if answer in {"yes", "y", "1", "first", "one"}:
            return {"selected_text": candidates[0], "needs_follow_up": False, "question": None}
        if answer in {"no", "n", "2", "second", "two"} and len(candidates) == 2:
            return {"selected_text": candidates[1], "needs_follow_up": False, "question": None}
        return {
            "selected_text": "",
            "needs_follow_up": True,
            "question": f"Did you mean {candidates[0]} or {candidates[1]}?",
        }

    @api.post("/v1/voices/enrollment")
    async def enroll_voice(payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("consent") is not True:
            raise HTTPException(status_code=403, detail="voice enrollment requires explicit consent")
        voice_id = payload.get("voice_id") or os.getenv("VOICEBACK_CARTESIA_VOICE_ID") or os.getenv("CARTESIA_VOICE_ID") or DEFAULT_CARTESIA_VOICE_ID
        return {
            "user_id": str(payload.get("user_id", "")),
            "consented": True,
            "voice_id": voice_id,
            "ready": bool(voice_id and (os.getenv("VOICEBACK_CARTESIA_API_KEY") or os.getenv("CARTESIA_API_KEY"))),
        }

    @api.post("/v1/speech")
    async def create_speech(payload: dict[str, Any]) -> dict[str, str]:
        if payload.get("approved") is not True:
            raise HTTPException(status_code=409, detail="explicit approval is required before speech")
        text = str(payload.get("text", "")).strip()
        api_key = os.getenv("VOICEBACK_CARTESIA_API_KEY") or os.getenv("CARTESIA_API_KEY")
        voice_id = payload.get("voice_id") or os.getenv("VOICEBACK_CARTESIA_VOICE_ID") or os.getenv("CARTESIA_VOICE_ID") or DEFAULT_CARTESIA_VOICE_ID
        if not text or not api_key or not voice_id:
            raise HTTPException(status_code=503, detail="Cartesia API key and consented voice ID are required")
        import httpx

        body = {
            "model_id": os.getenv("VOICEBACK_CARTESIA_MODEL") or os.getenv("CARTESIA_MODEL") or "sonic-2",
            "transcript": text,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": {"container": "mp3", "encoding": "mp3", "sample_rate": 44100},
        }
        headers = {
            "X-API-Key": api_key,
            "Cartesia-Version": os.getenv("VOICEBACK_CARTESIA_VERSION") or "2025-04-16",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("https://api.cartesia.ai/tts/bytes", json=body, headers=headers)
            response.raise_for_status()
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Cartesia speech provider failed") from exc
        return {"audio_base64": base64.b64encode(response.content).decode("ascii"), "content_type": "audio/mpeg"}

    return api


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
