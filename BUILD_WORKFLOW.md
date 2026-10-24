# VoiceBack build workflow

This is the authoritative, sequential engineering playbook. Every stage follows:

**IMPLEMENT → RUN → OBSERVE → VERIFY → DOCUMENT → NEXT STAGE**

Only one stage may be active at a time, except prerequisite fixes. A stage is `VERIFIED COMPLETE` only when its stated evidence exists. Simulator-only evidence never proves physical camera behavior; successful provider calls never prove model accuracy.

## Shared validation rules

Use the repository root as the working directory. Replace placeholders only with real local values; never commit secrets.

```bash
cd "/Users/raahil/Desktop/University of Pennsylvania/Freshman Year - 2026-2027/ESE/CalHacks/VoiceBack"
python3 -m pip install -e 'backend[dev]'
python3 -m pytest backend/tests
git status --short
git diff --check
```

For any external or physical test, record date, hardware/OS, commit, exact command, input fixture, output, and limitation in `PROGRESS.md`.

## STAGE 00 — Repository, Xcode and backend foundation

### Objective and expected result

Establish a reproducible repository, a real buildable Xcode app, a FastAPI health service, typed API/config boundaries, secret-safe ignores, and initial tests. The expected result is an app that launches in a simulator and a backend whose `/health` responds.

### Prerequisites

macOS, full Xcode 16+ selected with `xcode-select`, Git, Python 3.11+, and network access for Python packages. If full Xcode or a simulator runtime is unavailable, mark native validation `BLOCKED` or `IMPLEMENTED — UNVERIFIED`.

### Files/modules

Existing foundation paths: `ios/VoiceBack.xcodeproj`, `ios/VoiceBack/App/VoiceBackApp.swift`, `ios/VoiceBack/Views/`, `ViewModels/`, `Services/`, `Models/`, `Components/`, `Resources/Info.plist`, `ios/VoiceBackTests/`, `backend/app/main.py`, `config.py`, `backend/pyproject.toml`, `backend/tests/test_health.py`, `.env.example`, `.gitignore`.

Create typed Pydantic schemas in `backend/app/schemas/`, a versioned API router in `backend/app/api/`, and replace placeholder UI wiring only as needed to satisfy the foundation.

### Execution order

1. Inspect `git status`, current Xcode selection, Python version, and existing files.
2. Select full Xcode and ensure the project opens; do not regenerate or delete unrelated projects.
3. Build the app for an available simulator. Fix project configuration errors before feature work.
4. Add camera permission and video-only capture configuration. Do not add `AVAudioSession`, microphone permission, or audio input.
5. Add typed request/response models and `/health` plus a startup command.
6. Run backend tests, inspect response, and verify `.env` is ignored.
7. Commit only setup files and update `PROGRESS.md`.

### Commands

```bash
xcode-select -p
xcodebuild -list -project ios/VoiceBack.xcodeproj
xcodebuild -project ios/VoiceBack.xcodeproj -scheme VoiceBack -sdk iphonesimulator -configuration Debug -derivedDataPath /tmp/VoiceBackDerived CODE_SIGNING_ALLOWED=NO build
python3 -m pip install -e 'backend[dev]'
python3 -m pytest backend/tests
python3 -m uvicorn app.main:app --app-dir backend --port 8000
curl -fsS http://127.0.0.1:8000/health
git check-ignore .env
```

### Physical/device validation

Not required for completion of the foundation, but do not claim camera behavior from simulator results. On a device, verify camera permission text and that no microphone permission prompt appears.

### Tests and failure cases

Test health schema, invalid config, app launch, and clean/no-secret Git status. Troubleshoot missing full Xcode, signing errors with `CODE_SIGNING_ALLOWED=NO`, unavailable simulator runtime, Python dependency conflicts, and accidental `.env` tracking.

### Acceptance and Definition of Done

- `xcodebuild` simulator build succeeds and the app launches.
- `/health` returns HTTP 200 and typed JSON.
- At least one backend test passes.
- `.env` is ignored; no key, recording, weight, or build artifact is tracked.
- `PROGRESS.md` contains commands and evidence.

Next stage depends on the app/backend foundation only; it must not begin until the gate is verified or an explicit blocker is documented.

## STAGE 01 — Get real silent lip-reading working

### Objective and expected result

Prove or disprove useful visual-only transcription before extensive UI work. A genuine pretrained inference runs from video to predicted text without accessing audio, and a feasibility report records results for ordinary speech with audio removed and genuinely silent articulation.

### Prerequisites

Stage 00 foundation, a compatible Python/PyTorch environment, local or remote GPU access, storage for a checkpoint, sample videos with independently known ground truth, and permission to use all samples. No model weights are committed.

### Files/modules

Use `inference/README.md`, `inference/model_adapter.py`, `inference/setup_model.sh`, `backend/app/services/video_preprocessor.py`, and `visual_speech_model.py`. Add `inference/requirements-<environment>.txt` or a documented environment lock, adapter tests, fixtures metadata, and `docs/INFERENCE_FEASIBILITY.md`.

### Execution order

1. Inspect the official Auto-AVSR repository, license, requirements, configs, checkpoint URL, checksum, input dimensions, frame rate, color order, normalization, and audio assumptions.
2. Create an isolated environment matching the verified Python/PyTorch/CUDA versions; record versions and GPU.
3. Download the official compatible visual-only checkpoint, verify checksum, and keep it outside Git.
4. Run the original inference implementation unchanged on a known-ground-truth video.
5. Remove all audio tracks with FFmpeg and verify the output has no audio stream.
6. Re-run visual inference and inspect whether the implementation ever opens/reads audio.
7. Implement mouth-region extraction and normalization exactly as the selected model requires.
8. Wrap the verified implementation behind `ModelAdapter.transcribe_video`, returning raw text, candidate hypotheses, scores only when truly available, model version, and timing.
9. Run unseen samples: ordinary speech with audio removed and genuinely silent mouthed speech. Compute WER and sentence accuracy against independent ground truth.
10. Record representative successes, failures, latency, preprocessing metadata, and domain mismatch risks.

### Commands and tests

```bash
ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 sample_silent.mp4
ffmpeg -i input.mp4 -an -c:v copy output_no_audio.mp4
python -m pytest inference backend/tests
python -m inference.run_inference --video sample_no_audio.mp4 --checkpoint "$MODEL_CHECKPOINT_PATH"
```

The exact upstream command must be recorded after inspection; do not invent flags. Test checkpoint loading, frame shape/normalization, no-audio input, adapter response schema, and deterministic fixture metadata.

### Failure cases and feasibility checkpoint

A checkpoint loading successfully is not success. Investigate wrong crop, frame rate, resolution, color order, decoder, checkpoint mismatch, GPU memory, and domain mismatch. If genuine silent articulation is not useful, mark the stage `BLOCKED` or `IMPLEMENTED — UNVERIFIED`, quantify failure, and propose a revised experiment. Do not substitute Gemini, hardcoded strings, or prerecorded responses.

### Acceptance and Definition of Done

- At least one real pretrained video-to-text inference is evidenced.
- Audio-free input is verified and no microphone/audio path is used.
- A reusable adapter returns actual raw output and available hypotheses.
- Unseen-sample results include both audio-removed ordinary speech and genuine silent mouthing.
- Feasibility, WER, latency, limitations, and checkpoint provenance are documented.

Stage 02 depends on a real adapter contract and an explicit feasibility decision, not necessarily on high accuracy.

## STAGE 02 — iOS video recording and VSR integration

### Objective and expected result

Record a short front-camera utterance on a real iPhone, encode audio-free video, upload it, run the real backend VSR path, and display the actual response with retryable errors.

### Prerequisites

Stages 00 and 01, a reachable backend/GPU, an iPhone, Apple developer signing, camera permission, and a known device/network test plan.

### Files/modules

Edit `ios/VoiceBack/Services/CameraCaptureService.swift`; add recording/session, `URLSession` API client, upload models, `RecordingViewModel`, camera preview, error/retry views, backend upload router/schema, FFmpeg preprocessing, and integration tests. Keep microphone input absent.

### Execution order

1. Request camera permission and configure the front video input only.
2. Implement preview and start/stop recording with bounded utterance duration and stable frame rate.
3. Write a video-only file and inspect it with `ffprobe`.
4. Add multipart upload and backend size/type/duration validation.
5. Normalize frames to model requirements, then call the real adapter.
6. Decode typed transcript response and show original text, candidates, confidence metadata, and errors.
7. Handle permission denied, no face, interrupted recording, timeout, network failure, invalid video, and backend 5xx.

### Validation

```bash
python -m pytest backend/tests
ffprobe -v error -show_streams recorded.mp4
xcodebuild test -project ios/VoiceBack.xcodeproj -scheme VoiceBack -destination 'platform=iOS Simulator,name=iPhone 16'
```

On an actual iPhone, silently mouth an unseen sentence, record, submit, and compare the displayed transcript with the backend log. Verify no microphone prompt and no audio stream.

### Acceptance and Definition of Done

An actual iPhone produces an upload accepted by the backend and displays actual model output. Error paths are tested, audio absence is evidenced, and simulator results are labeled simulator-only. Next stage requires the real transcript contract and error handling.

## STAGE 03 — Gemini interpretation and error correction

### Objective and expected result

Add a backend-only structured Gemini interpretation that uses real VSR evidence and context without replacing it. The UI shows raw versus proposed text and uncertainty.

### Prerequisites

Stage 02 real transcript path, a valid backend-only `GEMINI_API_KEY`, provider SDK/version documentation, and a labeled evaluation set with independent ground truth.

### Files/modules

Edit `backend/app/services/gemini_client.py`; add schemas/router, prompt/version fixtures, redaction and timeout logic, `ios/VoiceBack/Models/Interpretation.swift`, API client, and comparison UI. Update `docs/API_CONTRACT.md`.

### Execution order

1. Confirm current official Google GenAI SDK and supported Gemini Flash model.
2. Define a strict structured response: proposed text, ambiguity candidates, rationale/evidence references, and uncertainty category—not calibrated probability.
3. Send raw output, candidates/scores when real, confirmed history, and approved context; redact unnecessary sensitive data.
4. Reject malformed/unsupported output and retry only with bounded policy.
5. Add a developer comparison screen/log that preserves raw text.
6. Evaluate raw and corrected output on known ground truth for negatives, names, numbers, homophones, and similar-looking words.

### Acceptance and Definition of Done

Real backend calls return validated structured interpretations; no key ships in iOS; evaluation records whether Gemini improves or damages WER/sentence correctness; critical invented words and silent rewrites are rejected. Next stage requires uncertainty/candidate data.

## STAGE 04 — Active clarification and gesture answers

### Objective and expected result

When evidence is ambiguous, the system asks a short grounded question and resolves it via calibrated nod/shake or touch fallback, then requires explicit final approval.

### Prerequisites

Stage 03 structured ambiguity, real iPhone with front camera, Vision/ARKit availability, and accessibility test participants or a careful test protocol.

### Files/modules

Add clarification schemas/service/router, Swift `ClarificationView`, `GestureRecognitionService`, calibration/session models, candidate state machine, touch controls, and unit/integration tests. Keep gesture acceptance disabled outside active clarification.

### Execution order

1. Detect ambiguity only from candidate evidence; generate a question grounded in candidates.
2. Display question, candidate context, large yes/no controls, and touch fallback.
3. Calibrate neutral head pose and nod/shake thresholds per session.
4. Apply temporal smoothing, minimum amplitude/duration, cooldown, and stale-question identifiers.
5. Accept a gesture only when clarification is active and confidence/temporal criteria pass.
6. Update or eliminate candidates; ask again only when necessary.
7. Provide “none of these”, correction, retry, and cancellation.
8. Present final sentence and require explicit approval; approval is never inferred from a head gesture used for clarification.

### Tests and demonstration

Test nod=yes, shake=no, neutral ignored, natural movement ignored, uncertain gesture rejected, stale response rejected, candidate eliminated, no candidate, and unreliable head control with touch fallback. Demonstrate: ambiguous transcript → Gemini question → physical gesture → candidate → explicit approval. No Cartesia call may occur before approval.

### Acceptance and Definition of Done

The full clarification interaction is evidenced on a device, gesture false acceptance is measured, touch fallback works, and approval gating is covered by tests.

## STAGE 05 — Cartesia enrollment and speech generation

### Objective and expected result

Enroll a consenting voice through the backend, store a secure reference, synthesize only user-approved text, deliver audio, play it on iPhone, and support deletion/fallback.

### Prerequisites

Stage 04 approval gate, valid Cartesia credentials, current official SDK/API docs, consent language, secure storage decision, and an audio test device.

### Files/modules

Edit `cartesia_client.py` and `voice_manager.py`; add enrollment/synthesis schemas/router, secure provider reference store, deletion path, `AudioPlaybackService`, voice onboarding and playback UI, and tests.

### Execution order

1. Validate consented sample format, duration, ownership, and deletion request.
2. Call Cartesia only from backend; never put keys in iOS.
3. Persist only the minimum secure provider reference and consent audit metadata.
4. Generate audio from final approved text; reject pending/uncertain text.
5. Stream/download validated audio to iOS and play it.
6. Implement user deletion and provider deletion where supported.
7. Add clearly labeled standard voice fallback when no original voice exists.

### Acceptance and Definition of Done

A consenting user enrolls, a previously unseen approved sentence is synthesized and played on iPhone, deletion is exercised, and logs prove only approved text was sent. Do not claim perfect voice reconstruction.

## STAGE 06 — End-to-end application

### Objective and expected result

Integrate all verified stages into the explicit state machine and recover cleanly from errors.

### Prerequisites

Stages 00–05 verified or explicitly approved with documented limitations, reachable services, test credentials, and physical iPhone.

### Files/modules

Add a central iOS workflow state model/view model, backend correlation IDs and request lifecycle, retry/cancel handling, analytics-safe diagnostics, and end-to-end tests.

### Execution order

Implement `READY → RECORDING → VIDEO_UPLOAD → VISUAL_DECODING → GEMINI_INTERPRETATION → CLARIFICATION_IF_NEEDED → USER_CONFIRMATION → CARTESIA_SYNTHESIS → AUDIO_PLAYBACK → READY`. Add timeout, retry, cancellation, no-face, unintelligible, no-candidate, provider failure, and return-to-ready behavior. Verify no synthesis for unconfirmed material uncertainty.

### Acceptance and Definition of Done

On a real iPhone with real model/provider calls, an unseen sentence completes through approved speech, and every listed failure path is observable and recoverable.

## STAGE 07 — Performance, accuracy and reliability

### Objective and expected result

Create a repeatable benchmark and optimize only measured bottlenecks.

### Prerequisites

Stage 06 working end-to-end, ground-truth dataset and consent, timing instrumentation, and repeatable model/provider environment.

### Measures and execution

Record visual-only WER, WER after Gemini, exact sentence accuracy, meaning-changing errors, clarification count, time to confirmed message, time to first audio, end-to-end time, failure/retry rate, gesture false acceptance/rejection, and latency for preprocessing, VSR, Gemini, interaction, and Cartesia. Separate machine processing time from human clarification time. Compare ordinary speech with removed audio to genuine silent mouthing and multiple users when feasible.

### Acceptance and Definition of Done

Benchmark artifacts, raw data, method, environment, results, limitations, and optimizations are committed. The approximately two-second machine-processing aspiration is only reported if measured; otherwise report actual timing.

## STAGE 08 — Final demo and GitHub

### Objective and expected result

Prepare an honest, reproducible hackathon demo and clean public repository.

### Prerequisites

Stages 00–07, consented demo participant and voice, validated device, documentation, licenses, and no secrets/artifacts in Git.

### Execution order

1. Prepare setup, demo, validation, limitations, and troubleshooting docs.
2. Record credits/licenses for pretrained models and providers.
3. Rehearse a live path: original voice consent → silent new sentence → real transcription → interpretation → clarification → approval → enrolled voice.
4. Capture logs/screenshots only with consent and redact sensitive data.
5. Verify clean Git status, commit history, public repository, and reproducible commands.

### Acceptance and Definition of Done

The demo uses real live inference and APIs, not scripted/prerecorded answers presented as live. README, architecture, setup, results, limitations, and credits are current; GitHub contains no secrets, recordings, weights, or build artifacts.

## Validation gate protocol

At the end of every stage, update `PROGRESS.md` with status, exact evidence, failures, limitations, commit hash, and next stage. Use exactly one status: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `IMPLEMENTED — UNVERIFIED`, or `VERIFIED COMPLETE`. Stop and request user approval before advancing.

