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

`model_adapter.py` exposes the stable `ModelAdapter.transcribe_video` boundary;
it stays `NotImplementedError` until a verified Auto-AVSR run is wired behind it.

## Modal GPU boundary

`modal_app.py` defines the `voiceback-inference` Modal app and a T4 GPU
function. It installs FFmpeg and the PyTorch runtime in the remote image, but
deliberately does not download model weights or fabricate transcripts. The
Auto-AVSR integration belongs to Stage 01 after the official model contract and
license are verified.

One-time local setup:

```bash
python3 -m pip install -r inference/requirements-modal.txt
modal token new
modal profile current
```

Validate the app definition without invoking GPU inference:

```bash
modal run inference/modal_app.py
```

Do not call `transcribe_video` until Stage 01 has a verified checkpoint and
test fixture. Modal secrets should be created only after credentials are
available; never place Gemini or Cartesia keys in this file.
