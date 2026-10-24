# Inference adapter

This package connects the backend to the official Auto-AVSR visual-only model.
Keep inference configurable for CPU, Apple MPS, and CUDA / remote-GPU
environments. **Do not download model weights during repository setup.** Weights
live in Git-ignored `checkpoints/` and are fetched only during Stage 01 with
explicit authorization.

Upstream details verified on 2026-10-24 are recorded in
[`../docs/INFERENCE_FEASIBILITY.md`](../docs/INFERENCE_FEASIBILITY.md). Summary:

- **Upstream:** `https://github.com/mpc001/auto_avsr` (Apache-2.0).
- **Architecture:** 3D conv → ResNet-18 → Conformer encoder → Transformer
  decoder (CTC + attention).
- **Visual-only inference:** `python eval.py --modality=video
  --pretrained-model-path=<ckpt> --root-dir=<root> --test-file=<list>`.
- **Dependencies:** `torch torchvision torchaudio pytorch-lightning sentencepiece
  av` (plus the repo's face-landmark preprocessing dependencies). Exact version
  pins are locked per environment once a compute target is chosen.
- **Visual-only checkpoints (model zoo):** `vsr_trlrs2lrs3vox2avsp_base.pth`
  (best, ~20% WER on LRS3), `vsr_trlrs3vox2_base.pth`, `vsr_trlrs3_23h_base.pth`.
  Those WER figures are the authors' LRS3 (scripted, originally-audible) numbers
  and are **not** evidence for genuine silent mouthing.

**Pending verification from upstream `preparation/` source (do not hardcode
until confirmed):** mouth crop size, grayscale vs color, frame rate,
normalization, face-detection/landmark tooling, and that the `video` loader
never reads the audio track.

`model_adapter.py` exposes the stable `ModelAdapter.transcribe_video` boundary.
The adapter uses the official video preprocessing components, PyAV frame decoding,
and a CUDA-capable device when available; it does not open or decode microphone
audio.

## Modal GPU boundary

`modal_app.py` defines the `voiceback-inference` Modal app and a T4 GPU
function. It installs FFmpeg, PyTorch, compatible legacy MediaPipe, and the
official Auto-AVSR source in the remote image. On the first real invocation it
caches the official `vsr_trlrs3_base.pth` checkpoint in the Modal volume
`voiceback-model-cache`, strips audio from the submitted video, and runs the
visual-only adapter. It never fabricates a transcript.

Validation completed on 2026-10-24: Modal authentication, image build, source
upload, checkpoint download, CUDA/MediaPipe initialization, and the video-only
execution path all ran on a Tesla T4. A public sample fixture reached face
detection but contained no detectable face, so no transcript is reported as
successful. A consented front-camera fixture is still required for Stage 01
benchmark evidence.

One-time local setup:

```bash
python3 -m pip install -r inference/requirements-modal.txt
modal token new
modal profile current
```

Validate the app definition without invoking model inference:

```bash
modal run inference/modal_app.py
```

The first call to `transcribe_video.remote(video_bytes)` uses a T4 GPU and
Modal compute credits. Use only a consented fixture. The official demo
checkpoint smoke test is separate from VoiceBack's genuine silent-mouthing
feasibility benchmark. Modal secrets should be created only after credentials
are available; never place Gemini or Cartesia keys in this file.
