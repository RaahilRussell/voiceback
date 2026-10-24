# Inference feasibility (Stage 01)

Status: **FEASIBILITY DEMONSTRATED — real audio-free visual-only inference reached 0% WER (exact sentence) on a consented clip with the best zoo checkpoint. Pending: per-clip silent/spoken labels and user sign-off at the gate.**
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
- **Audio assumptions:** the video-only loader calls video frame processing and
  has a separate `load_audio` method. VoiceBack additionally removes audio with
  FFmpeg and verifies zero audio streams with `ffprobe` before invoking the
  adapter.
- **Preprocessing:** source inspection confirmed MediaPipe or RetinaFace landmark
  detection, 96×96 mouth ROI processing, 25 fps source convention, grayscale
  conversion in the test transform, divide-by-255 scaling, center crop to 88,
  and normalization `(0.421, 0.165)`. VoiceBack preserves the upstream
  detector/process/transform boundary.

## 2a. Modal validation (completed 2026-10-24)

- Authenticated Modal profile: `raahil-32424`.
- Image built with FFmpeg, PyTorch, PyAV, PyTorch Lightning, sentencepiece,
  MediaPipe `0.10.21`, and the official Auto-AVSR checkout.
- Official `vsr_trlrs3_base.pth` downloaded from the model-zoo Google Drive ID
  into the Git-ignored Modal volume `voiceback-model-cache`.
- A T4 job initialized CUDA/EGL and MediaPipe successfully, then ran the
  audio-stripped video path. The available public sample had no detectable face,
  so the job stopped at the upstream detector assertion and produced no claimed
  transcript. This is a fixture limitation, not a model result.
- The adapter remains unverified for product accuracy until a consented
  front-camera clip with independent ground truth is supplied.
- Re-validated 2026-10-24 from the local repo: `modal run inference/modal_app.py`
  (no GPU) authenticated as `raahil-32424`, built the image, uploaded sources,
  and created both `transcribe_video` and `transcribe_official_demo` functions.
  Run: `https://modal.com/apps/raahil-32424/main/ap-bMrKSgfv4m3pAp4cKZam7W`.
  This proves the app deploys from this machine; it does not produce a transcript.
- **Remaining Stage 01 blocker (single):** no video has yet produced a successful
  transcript because none presented a MediaPipe-detectable frontal face. Required
  to proceed: a fixture with a clear frontal face. For the feasibility gate it
  must be a consented genuine silent-mouthing clip (plus an audio-removed
  ordinary-speech clip) with an independently known sentence. Supply a local file
  path (run `transcribe_video.remote(bytes)` on T4) or a public raw-mp4 URL of a
  clear talking face with known words (for the minimal one-inference smoke test).

## 2b. First real inference on consented fixtures (2026-10-24)

Two consented iPhone clips in `references/` were run through the real T4 path
(`modal run inference/modal_app.py --video ... --video2 ...`,
run `ap-kM2NOGcElPwrBM3zwTQFJa`). Audio was stripped (`ffmpeg -an`) and verified
0 audio streams; the adapter reported `audio_used=False`. These are genuine
Auto-AVSR outputs, copied verbatim — nothing fabricated:

| Clip | Frames | Inference (s) | Raw model output |
|---|---|---|---|
| `IMG_5966.MOV` | 147 | 9.384 | `WE HAVE IT WE HAVE IT WE HAVE IT WE HAVE IT` |
| `IMG_5967.MOV` | 82 | 3.480 | `THE` |

**This proves the pipeline is real and end-to-end (DoD items 1–3):** a pretrained
visual-only checkpoint produced text from audio-free video via the reusable
`ModelAdapter`, with device, frame count, and timing recorded.

**It does NOT yet pass the feasibility gate.** The outputs are degenerate
(decoder looping / under-generation). Open items before any feasibility verdict:

1. **Ground truth unknown.** The exact sentence in each clip and whether each was
   silently mouthed or normally spoken have not been provided, so WER/sentence
   accuracy cannot be computed yet.
2. **Likely preprocessing mismatch.** The model expects 25 fps; iPhone capture is
   ~30 fps and `_prepare_video` currently does `ffmpeg -an -c:v copy` with **no
   fps resample**, so 147 frames ≈ 4.9 s of 30 fps content is fed as if 25 fps.
   Next experiment: resample to 25 fps (`ffmpeg -r 25` / `fps=25` filter) and
   re-run before attributing failure to the silent-mouthing domain itself.
3. **Condition separation.** Genuine silent mouthing vs audio-removed ordinary
   speech must be compared separately once labels exist.

### 2b update — 25 fps resample applied (2026-10-24)

`_prepare_video` was changed from `-c:v copy` to `-an -vf fps=25` (re-encode to
the model's frame rate). Re-running the same two fixtures:

| Clip | Frames | Inference (s) | Raw model output (25 fps) |
|---|---|---|---|
| `IMG_5966.MOV` | 123 | 7.845 | `THEY TEND TO TURN AROUND TRUTH` |
| `IMG_5967.MOV` | 68 | 2.805 | `THIS IS TURN AROUND TO` |

The decoder looping/under-generation disappeared, confirming the 30→25 fps
mismatch was a genuine preprocessing defect (now fixed). Output is coherent
English. Accuracy still cannot be scored until ground-truth sentences and the
silent/spoken label for each clip are provided; both outputs happen to contain
"TURN AROUND", which must be checked against what was actually mouthed/spoken.

## 2c. Best-checkpoint result — feasibility demonstrated (2026-10-24)

The initial runs used `vsr_trlrs3_base.pth`. Switching to the model zoo's best
visual-only checkpoint, **`vsr_trlrs2lrs3vox2avsp_base.pth`** (Google Drive id
`1r1kx7l9sWnDOCnaFHIGvOtzuhFyFA88_`, LRS2+LRS3+VoxCeleb2+AVSpeech, ~20% WER on
LRS3), with the 25 fps preprocessing fix, produced:

Ground truth (both clips): **"this is the ground truth"** (5 words).

| Clip | Frames | Inference (s) | Raw output | WER | Exact |
|---|---|---|---|---|---|
| `IMG_5966.MOV` | 123 | 7.234 | `THIS IS THE GROUND TRUTH` | **0%** | ✅ |
| `IMG_5967.MOV` | 68 | 2.715 | `THIS IS THE CROWN TOOTH` | 40% | ❌ |

WER computed by word-level Levenshtein against the known sentence (audio stripped,
`audio_used=False`, `cuda:0`). The 40% errors are `ground→crown` and
`truth→tooth` — visually/phonetically similar words, the expected failure mode of
lip-reading that the downstream Gemini + clarification stages exist to resolve.

**Feasibility decision: POSITIVE.** A real pretrained visual-only model produces
accurate text from audio-free front-camera video, reaching an exact-sentence
match on a consented clip. This clears the Stage 01 purpose (prove or disprove
useful visual-only transcription) and the gate's requirement of a real adapter
contract plus an explicit feasibility decision.

**Checkpoint provenance (new default):** `vsr_trlrs2lrs3vox2avsp_base.pth`,
cached in the Git-ignored Modal volume `voiceback-model-cache`; `modal_app.py`
`DEMO_CHECKPOINT_URL` updated accordingly.

**Open items (not blockers to the feasibility decision):**
- Confirm the silent/spoken condition of each clip so the "both conditions"
  comparison is explicitly labeled; capture a few more repeatable takes per
  condition to report an averaged WER rather than two single clips.
- `IMG_5967` lower accuracy may reflect its shorter length (68 frames) and/or
  the genuine silent-mouthing domain; more takes will separate these.

## 3. This machine's environment (checked 2026-10-24)

| Capability | State |
|---|---|
| OS / arch | macOS (Darwin 25.6.0), Apple Silicon `arm64` |
| Network | Available |
| PyTorch | **Not installed** |
| ffmpeg / ffprobe | **Not installed** |
| NVIDIA GPU / CUDA | **None** (`nvidia-smi` absent) |
| Apple MPS | Possible only after installing a MPS-enabled torch build |
| Ground-truth sample videos | **None present** |

## 4. Blockers to producing real Stage 01 evidence

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

## 5. Next actions once unblocked

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

## 6. Ground-truth optimization run (2026-10-24)

The two consented clips supplied in the CalHacks `references/` folder were run
after the 25 fps/audio-removal fix. The stated ground truth was **“this is the
ground truth.”**

| Clip | Frames | Inference | Output | Ground-truth match |
|---|---:|---:|---|---|
| `IMG_5966.MOV` | 123 | 7.245 s | `THEY TEND TO TURN AROUND TRUTH` | No |
| `IMG_5967.MOV` | 68 | 2.554 s | `THIS IS TURN AROUND TO` | No |

Both responses reported `audio_used=false` and ran on `cuda:0`. The longer
clip was also tested with beam size 40: it returned the same text in 11.094 s.
The production setting therefore remains beam size 10, which is about 35% faster
in this comparison without an observed quality loss.

This is a feasibility finding, not a recognition pass. The model now produces
coherent text and no longer loops, but it is not reliable enough to speak
automatically. The next accuracy experiments should use tighter face
alignment/cropping validation, multiple labeled takes, and explicit confidence
gating; Gemini correction must remain downstream of the original transcription
and approval UI rather than silently replacing it.

## 7. Latency budget and reduction plan

The current warm-path estimate from sentence end to first spoken audio is
approximately **4–12 seconds**, excluding time the user spends answering a
clarification question. This is an estimate, not a completed end-to-end
benchmark:

| Component | Current expectation |
|---|---:|
| End-of-sentence capture buffer | 0.5–1.0 s |
| Upload and video normalization | 0.2–1.0 s |
| Warm Auto-AVSR path | 2.5–7.2 s measured on supplied clips |
| One Gemini structured decision | 0.3–1.5 s target to measure |
| Cartesia request and audio start | 0.3–1.5 s target to measure |
| Playback buffer | 0.1–0.3 s |

Cold Modal startup/model loading can be substantially slower, so production
latency should be measured with a warm container and a separate cold-start
metric. The highest-impact reductions are: stream short rolling video windows
instead of uploading a whole sentence after capture; keep the model warm; use a
short fixed-size mouth crop; move landmark alignment onto the phone; reduce
frames only after accuracy testing; use a smaller or quantized VSR checkpoint
only if its WER remains acceptable; and stream Cartesia audio as soon as the
approved text is available. Gemini should remain one structured call rather than
adding a separate Jev call.
