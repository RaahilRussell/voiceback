"""WebSocket session transport for incremental silent-speech capture.

The current Auto-AVSR checkpoint is an utterance-level offline model. This
module therefore implements the real frame transport and event state machine,
but labels recognition as final until a causal/incremental decoder is proven.
It never fabricates partial words or calls repeated offline decoding a true
next-token model.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.services.gemini_client import GeminiClient
from app.services.visual_speech_model import VisualSpeechModel

MAX_FRAMES = 300
MAX_FRAME_BYTES = 1_500_000
MAX_TOTAL_BYTES = 25 * 1024 * 1024


class StreamingSession:
    """Bounded binary-frame session with explicit provisional/final events."""

    def __init__(
        self,
        websocket: WebSocket,
        model: VisualSpeechModel,
        gemini: GeminiClient,
        session_id: str,
    ) -> None:
        self.websocket = websocket
        self.model = model
        self.gemini = gemini
        self.session_id = session_id or str(uuid.uuid4())
        self.utterance_id = str(uuid.uuid4())
        self.revision = 0
        self.fps = 25
        self.frames: list[bytes] = []
        self.total_bytes = 0
        self.prefix_preview = False
        self.preview_task: asyncio.Task[None] | None = None
        self.model_lock = asyncio.Lock()

    def _event(self, name: str, **payload: Any) -> dict[str, Any]:
        self.revision += 1
        return {
            "schema_version": 1,
            "event": name,
            "session_id": self.session_id,
            "utterance_id": self.utterance_id,
            "revision": self.revision,
            "timestamp_ms": int(time.monotonic() * 1000),
            **payload,
        }

    async def emit(self, name: str, **payload: Any) -> None:
        await self.websocket.send_text(json.dumps(self._event(name, **payload)))

    async def run(self) -> None:
        await self.websocket.accept()
        await self.emit(
            "session_ready",
            state="tracking",
            capabilities={
                "binary_jpeg_frames": True,
                "partial_hypotheses": self.prefix_preview,
                "model_streaming": False,
                "final_decode": True,
            },
        )
        try:
            while True:
                message = await self.websocket.receive()
                if message.get("bytes") is not None:
                    await self._receive_frame(message["bytes"])
                    continue
                if message.get("text") is None:
                    continue
                control = json.loads(message["text"])
                message_type = control.get("type")
                if message_type == "start":
                    self.fps = max(1, min(int(control.get("fps", 25)), 30))
                    self.prefix_preview = bool(control.get("prefix_preview", False))
                    # Send the negotiated capability again after start so the
                    # client does not need to race the initial ready event.
                    await self.emit(
                        "session_ready",
                        state="tracking",
                        capabilities={
                            "binary_jpeg_frames": True,
                            "partial_hypotheses": self.prefix_preview,
                            "model_streaming": False,
                            "final_decode": True,
                        },
                    )
                    await self.emit("utterance_started", state="articulating")
                elif message_type == "end":
                    await self._finish()
                    return
                elif message_type == "cancel":
                    await self.emit("cancelled", state="cancelled")
                    return
        except WebSocketDisconnect:
            return
        except (ValueError, KeyError, TypeError) as exc:
            await self.emit("error", code="invalid_stream_message", message=str(exc))

    async def _receive_frame(self, frame: bytes) -> None:
        if not frame or len(frame) > MAX_FRAME_BYTES:
            await self.emit("error", code="frame_rejected", message="frame is empty or too large")
            return
        if len(self.frames) >= MAX_FRAMES or self.total_bytes + len(frame) > MAX_TOTAL_BYTES:
            await self.emit("error", code="stream_limit", message="bounded frame buffer is full")
            return
        self.frames.append(frame)
        self.total_bytes += len(frame)
        if (
            self.prefix_preview
            and len(self.frames) % self.fps == 0
            and (self.preview_task is None or self.preview_task.done())
        ):
            self.preview_task = asyncio.create_task(self._emit_prefix_preview())
        await self.emit(
            "capture_quality",
            state="articulating",
            frame_count=len(self.frames),
            bytes_received=self.total_bytes,
            partial_hypothesis=None,
            note="offline checkpoint; no partial word is claimed",
        )

    async def _finish(self) -> None:
        if not self.frames:
            await self.emit("error", code="no_frames", message="no video frames were received")
            return
        if self.preview_task is not None and not self.preview_task.done():
            self.preview_task.cancel()
        await self.emit(
            "partial_hypothesis",
            state="processing",
            text="",
            source="auto_avsr",
            generation_mode="offline_final_decode",
            note="the installed checkpoint does not expose causal next-token decoding",
        )
        try:
            video = await asyncio.to_thread(self._encode_video)
            async with self.model_lock:
                result = await asyncio.to_thread(self.model.predict, video)
        except Exception as exc:  # noqa: BLE001 - convert model failure to stream event
            await self.emit("error", code="visual_speech_failed", message=str(exc))
            return
        await self.emit(
            "final_candidates",
            state="proposed",
            source="auto_avsr",
            text=result.get("text", ""),
            candidates=result.get("candidates", []),
            candidate_scores=result.get("candidate_scores", []),
            audio_used=result.get("audio_used", False),
            frames=result.get("frames", len(self.frames)),
            inference_seconds=result.get("inference_seconds"),
            device=result.get("device"),
        )
        if self.gemini.api_key:
            try:
                kwargs = {
                    "original_text": str(result.get("text", "")),
                    "candidates": (result.get("candidates") or [result.get("text", "")])[:5],
                }
                if result.get("candidate_scores"):
                    kwargs["candidate_scores"] = result["candidate_scores"]
                interpretation = await self.gemini.interpret(**kwargs)
                await self.emit(
                    "context_result",
                    state="proposed",
                    source="gemini_candidate_reranker",
                    interpretation=interpretation.model_dump(),
                )
                await self.emit(
                    "decision",
                    state="clarification_required" if interpretation.needs_clarification else "proposed",
                    decision="needs_clarification" if interpretation.needs_clarification else "awaiting_approval",
                )
            except Exception as exc:  # noqa: BLE001 - preserve raw result on provider outage
                await self.emit(
                    "context_result",
                    state="proposed",
                    source="gemini_candidate_reranker",
                    available=False,
                    note=str(exc),
                )

    async def _emit_prefix_preview(self) -> None:
        """Experimental provisional decode over a growing offline prefix."""
        snapshot = list(self.frames)
        try:
            video = await asyncio.to_thread(self._encode_video, snapshot)
            async with self.model_lock:
                result = await asyncio.to_thread(self.model.predict, video)
            await self.emit(
                "partial_hypothesis",
                state="provisional",
                source="auto_avsr",
                text=result.get("text", ""),
                candidates=result.get("candidates", []),
                generation_mode="repeated_offline_prefix",
                model_streaming=False,
                note="experimental preview; not causal next-token decoding",
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - preview must not kill capture
            await self.emit("error", code="prefix_preview_failed", message=str(exc))

    def _encode_video(self, frames: list[bytes] | None = None) -> bytes:
        frames = self.frames if frames is None else frames
        with tempfile.TemporaryDirectory(prefix="voiceback-stream-") as directory:
            root = Path(directory)
            for index, frame in enumerate(frames):
                (root / f"frame-{index:06d}.jpg").write_bytes(frame)
            output = root / "stream.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(self.fps),
                    "-i", str(root / "frame-%06d.jpg"), "-an", "-c:v", "libx264",
                    "-preset", "ultrafast", str(output),
                ],
                check=True,
                capture_output=True,
            )
            return output.read_bytes()
