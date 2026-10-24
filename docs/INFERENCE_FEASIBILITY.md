# Inference feasibility (Stage 01)

Status: **IN PROGRESS — upstream inspection complete; blocked on inputs for real inference.**
Last updated: 2026-10-24

This document records the Stage 01 feasibility investigation for visual-only
(silent lip-reading) speech recognition. It is updated with real evidence as
the stage proceeds. No model output in this document may be fabricated; every
result must come from an actual run and cite its command, input, and date.

## 1. Upstream model inspection (completed 2026-10-24)

Source of truth: the official Auto-AVSR repository and its paper. Values below
were read from the repository README and project page on 2026-10-24; anything
not stated there is marked **PENDING (read from source)** and must be confirmed
in code before implementation — it must not be guessed.

- **Official repository:** `https://github.com/mpc001/auto_avsr` (Pingchuan Ma,
  Imperial College London). Successor to "End-to-End Audio-Visual Speech
  Recognition with Conformers."
- **License:** Apache-2.0 (permissive; attribution + license notice required).
- **Architecture:** 3D convolution → ResNet-18 visual frontend → Conformer
  encoder → Transformer decoder, joint CTC + cross-entropy training.
- **Inference entry point (README):**
  `python eval.py --modality=video --root-dir=[root] --test-file=[list] --pretrained-model-path=[ckpt]`.
  A tutorial notebook ("Audio/Visual Speech Recognition") and a "Cropping Mouth
  from Video" tutorial are referenced for single-file inference.
- **Dependencies (README):** `torch torchvision torchaudio pytorch-lightning
  sentencepiece av`; recommended `conda create -n autoavsr python=3.8`. The repo
  ships **no** `requirements.txt`/`environment.yml`, so exact version pins must
  be derived and then locked in `inference/requirements-<environment>.txt`.
- **Visual-only (VSR) checkpoints — model zoo (Google Drive):**

  | Checkpoint | Reported WER | Training data |
  |---|---|---|
  | `vsr_trlrs3_23h_base.pth` | 93.0% | LRS3 23h (not usable) |
  | `vsr_trlrs3vox2_base.pth` | 24.6% | LRS3 + VoxCeleb2 |
  | `vsr_trlrs2lrs3vox2avsp_base.pth` | 20.3% | LRS2+LRS3+VoxCeleb2+AVSpeech (best) |

  WER figures are the authors' numbers on the **LRS3 test set** (read, scripted
  speech with audio originally present). They are **not** evidence for this
  product's population (genuine silent mouthers) and must not be reported as
  such. Stage 01's job is to measure our own conditions.
- **Audio assumptions:** `--modality` has independent `video` and `audio`
  values, implying the video path is visual-only. **PENDING (read from source):**
  confirm the `video` data loader never opens/decodes the audio stream (Stage 01
  execution step 6). This must be verified in code, not assumed.
- **Preprocessing (crop size, grayscale, fps, face-detection/landmark tooling):**
  **PENDING (read from source)** in the repo's `preparation/` pipeline. The
  standard visual-speech ROI convention is a mouth-centred grayscale crop at 25
  fps, but the exact pixel size, normalization, and landmark dependency
  (e.g. RetinaFace + face alignment) will be taken verbatim from the upstream
  preparation code before any adapter wiring. Wrong crop/fps/color is the most
  common cause of a loaded-but-useless checkpoint.

## 2. This machine's environment (checked 2026-10-24)

| Capability | State |
|---|---|
| OS / arch | macOS (Darwin 25.6.0), Apple Silicon `arm64` |
| Network | Available |
| PyTorch | **Not installed** |
| ffmpeg / ffprobe | **Not installed** |
| NVIDIA GPU / CUDA | **None** (`nvidia-smi` absent) |
| Apple MPS | Possible only after installing a MPS-enabled torch build |
| Ground-truth sample videos | **None present** |

## 3. Blockers to producing real Stage 01 evidence

Stage 01's Definition of Done requires at least one real pretrained
video→text inference, verified audio-free input, a reusable adapter returning
real output, and WER on **both** (a) ordinary speech with audio removed and
(b) genuine silent mouthing, against independent ground truth. The following
are required to produce that evidence and cannot be fabricated or substituted:

1. **Labeled sample videos (user-provided).** Front-camera clips with
   independently known ground-truth sentences, including a genuine
   silent-mouthing set recorded by a consenting person, plus permission to use
   them. This is the hardest and non-optional input; nothing downstream can
   substitute for it.
2. **Compute-target decision (user).** Local CPU, Apple MPS, or a remote CUDA
   GPU. This determines the torch build and the `requirements-<environment>.txt`
   lock, and whether latency numbers are meaningful.
3. **Authorization to install the heavy stack and download a checkpoint (user).**
   torch/torchvision/torchaudio + pytorch-lightning + sentencepiece + av,
   `ffmpeg` (for the audio-removal step), the `auto_avsr` repo and its
   face-landmark model files, and one VSR checkpoint (Google Drive, hundreds of
   MB). Weights stay outside Git (`checkpoints/`, `models/`, `artifacts/` are
   already ignored).

## 4. Next actions once unblocked

1. Create the chosen isolated environment; record Python/torch/CUDA/GPU versions.
2. Read `preparation/` to pin exact crop size, fps, color, normalization, and
   landmark dependency; record them here.
3. Download the selected checkpoint, record URL + checksum, keep it out of Git.
4. Run the upstream `eval.py`/tutorial unchanged on one labeled clip; record the
   exact command and raw output.
5. Strip audio with `ffmpeg -an`, verify with `ffprobe` that no audio stream
   remains, re-run, and confirm in code that the video loader never reads audio.
6. Wrap the verified path behind `ModelAdapter.transcribe_video`, returning raw
   text, candidate hypotheses, scores only when truly available, model version,
   and timing.
7. Evaluate audio-removed ordinary speech vs genuine silent mouthing; compute
   WER and sentence accuracy; record successes, failures, latency, and the
   feasibility decision.
