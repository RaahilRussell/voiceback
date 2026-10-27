"""Lazy adapter around the official Auto-AVSR visual-only inference path.

Auto-AVSR is loaded lazily because the laptop environment does not need the
heavy PyTorch stack. The Modal image supplies the upstream repository and its
runtime dependencies. The adapter follows the repository's inference tutorial
and never calls an audio loader.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


class ModelAdapter:
    """Stable VoiceBack interface for visual-only Auto-AVSR inference."""

    def __init__(self, checkpoint_path: str | None = None, device: str = "auto", upstream_root: str = "/opt/auto_avsr", beam_size: int = 10) -> None:
        self.checkpoint_path = checkpoint_path
        self.device = device
        self.upstream_root = upstream_root
        self.beam_size = beam_size
        self._pipeline = None

    def _build_pipeline(self):
        if not self.checkpoint_path:
            raise ValueError("checkpoint_path is required for real inference")
        if not Path(self.checkpoint_path).is_file():
            raise FileNotFoundError(self.checkpoint_path)

        import torch

        sys.path.insert(0, self.upstream_root)
        sys.path.insert(0, str(Path(self.upstream_root) / "preparation"))
        from datamodule.transforms import VideoTransform
        from lightning import ModelModule, get_beam_search_decoder
        from preparation.data.data_module import AVSRDataLoader

        if self.device in {"cuda", "cuda:0"} and torch.cuda.is_available():
            device = "cuda:0"
        elif self.device in {"mps", "auto"} and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        class _Config(dict):
            __getattr__ = dict.__getitem__

        args = _Config(modality="video", pretrained_model_path=None, ctc_weight=0.1)
        model_module = ModelModule(args)
        checkpoint = torch.load(self.checkpoint_path, map_location="cpu")
        model_module.model.load_state_dict(checkpoint)
        model_module.model.to(device).eval()

        return {
            "torch": torch,
            "device": device,
            "model": model_module,
            "beam_search": get_beam_search_decoder(
                model_module.model, model_module.token_list, beam_size=self.beam_size
            ),
            "loader": AVSRDataLoader(modality="video", detector="mediapipe", convert_gray=False),
            "transform": VideoTransform(subset="test"),
        }

    def transcribe_video(self, video_path: str) -> dict[str, object]:
        """Transcribe a video using visual frames only."""

        import av
        import torch

        if self._pipeline is None:
            self._pipeline = self._build_pipeline()
        pipeline = self._pipeline
        started = time.perf_counter()
        # torchvision.io.read_video was removed from newer torchvision builds;
        # PyAV is already an Auto-AVSR dependency and keeps this path video-only.
        with av.open(video_path) as container:
            video = __import__("numpy").stack([frame.to_ndarray(format="rgb24") for frame in container.decode(video=0)])
        landmarks = pipeline["loader"].landmarks_detector(video)
        video = pipeline["loader"].video_process(video, landmarks)
        if video is None:
            raise ValueError("Auto-AVSR mouth preprocessing returned no video")
        video = torch.tensor(video)
        video = video.permute((0, 3, 1, 2))
        video = pipeline["transform"](video).to(pipeline["device"])
        inference_context = (
            torch.autocast(device_type="cuda", dtype=torch.float16)
            if pipeline["device"].startswith("cuda")
            else torch.autocast(device_type="cpu", enabled=False)
        )
        with torch.inference_mode(), inference_context:
            model = pipeline["model"].model
            features = model.frontend(video.unsqueeze(0))
            features = model.proj_encoder(features)
            encoded, _ = model.encoder(features, None)
            hypotheses = pipeline["beam_search"](encoded.squeeze(0))
            beam_candidates: list[dict[str, object]] = []
            seen: set[str] = set()
            for hypothesis in hypotheses[: self.beam_size]:
                token_ids = torch.tensor(list(map(int, hypothesis.yseq[1:])))
                candidate = pipeline["model"].text_transform.post_process(token_ids).replace("<eos>", "").strip()
                if not candidate or candidate in seen:
                    continue
                seen.add(candidate)
                score = hypothesis.score
                if hasattr(score, "detach"):
                    score = score.detach().cpu().item()
                beam_candidates.append(
                    {"text": candidate, "raw_score": float(score), "score_type": "beam_log_score"}
                )
            if not beam_candidates:
                raise ValueError("Auto-AVSR beam decoder returned no text candidates")
            text = str(beam_candidates[0]["text"])

        return {
            "text": text.strip(),
            "candidates": [item["text"] for item in beam_candidates],
            "candidate_scores": beam_candidates,
            "audio_used": False,
            "frames": int(video.shape[0]),
            "device": pipeline["device"],
            "inference_seconds": round(time.perf_counter() - started, 3),
            "model": "mpc001/auto_avsr",
        }
