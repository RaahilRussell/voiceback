# VoiceBack progress

Last updated: 2026-10-24

## Current state

- Current active stage: **STAGE 06 — end-to-end validation** (software path complete; physical iPhone test remains).
- Stage 01 approved and committed as `121cbf7` (0% WER exact-sentence audio-free transcript on a consented clip with the best checkpoint). Feasibility decision: POSITIVE.
- Stage 02 implemented 2026-10-24: backend `POST /v1/transcriptions` (multipart upload → deployed Modal T4 VSR → typed `TranscriptionResponse`), with size/type/empty/no-face(422)/provider-failure(502)/audio-used(500) handling; iOS front-camera **video-only** recording (`AVCaptureMovieFileOutput`, bounded 5 s, no mic/`AVAudioSession`), live preview, multipart upload client, and a ready/recording/uploading/result/failed state machine with retry. Info.plist keeps camera-only usage + `NSAllowsLocalNetworking` (no microphone key).
- Stage 02 evidence: backend suite **13 passed**; the backend provider uploaded the real 9.6 MB clip to the deployed Modal function and received `THIS IS THE GROUND TRUTH` (`audio_used:false`); iOS simulator **build + `xcodebuild test` SUCCEEDED** (Swift 6, no warnings). Simulator cannot exercise the camera, so device behavior is unverified.
- Stage 02 simulator run (2026-10-24): app installed + launched on iPhone 17 sim; requested **camera only** (no mic prompt) and fell to the graceful "No front camera is available" retry state (expected — simulators have no camera).
- Stage 02 device attempt (2026-10-24): Xcode account was present, but the first command used the certificate team ID instead of the active Personal Team. After switching to Personal Team `28N3GP9MWX` and changing the bundle ID to `com.raahilrussell.voiceback`, Xcode automatically created profile `iOS Team Provisioning Profile: com.raahilrussell.voiceback` and the physical-device build **SUCCEEDED**. The app **installed** on RaahiliPhone; launch was denied only because the phone was locked.
- Gemini/latency optimization (2026-10-24): fixed Modal structured-output parsing by reading the candidate part payload with JSON/literal fallback, increased the remote deadline to 30 s, and added deterministic temperature-0/seed-7 settings. Ordinary single-candidate sentences now use a safe fast path; known collisions such as `PRO`/`BRO` still invoke Gemini and remain clarification-gated. `transcribe_video` uses beam size 5 by default, with `VOICEBACK_BEAM_SIZE` as an override, keeps one warm worker for up to 15 minutes, and now targets an L4 GPU. Two live ground-truth requests returned HTTP 200 and `audio_used:false`; the warm L4 run measured 2.80 s model time and 7.08 s end-to-end, versus the prior warm T4 model time of 7.09 s.
- End-to-end contract completion (2026-10-24): implemented FFmpeg normalization, clarification resolution, explicit consent/voice state, Cartesia TTS request handling, `/v1/clarifications`, `/v1/voices/enrollment`, and approval-gated `/v1/speech`. Added iOS approved-text audio playback through `AVAudioPlayer`. Backend test suite passes **20 tests**, including mocked Cartesia audio returned as an iOS-compatible base64 payload. Configured the public Cartesia demo voice as the default fallback while preserving user voice-ID override.
- Final remote contract validation (2026-10-24): after one final Modal deploy, public `/health` returned 200, public `/v1/clarifications` resolved `I AM A PRO` from a yes answer, public `/v1/voices/enrollment` rejected missing consent with 403, and public `/v1/speech` rejected `approved:false` with 409. No GPU inference was consumed by these checks.
- Final Cartesia validation (2026-10-24): live Cartesia returned 22,196 bytes of MP3 for `VoiceBack test.` using the default demo voice; public Modal enrollment returned `ready:true`, and public approved speech returned HTTP 200 with an audio payload (`audio/mpeg`, 31,824 base64 characters). No personal voice clone is claimed until the user supplies one.
- Gemini safety/quality repair (2026-10-24): constrained both local and Modal Gemini paths to the supplied Auto-AVSR candidates, removed fabricated per-word checks from the deterministic fast path, filtered word checks to known lip-motion collisions that actually occur in the source text, and kept invalid model rewrites clarification-gated. Backend tests remain **20 passed**; sanitizer smoke tests passed for ordinary-word filtering and PRO/BRO clarification.
- Final Cartesia recheck after redeploy (2026-10-24): Modal app redeployed successfully; public `/health` returned 200, `/v1/clarifications` resolved the first candidate, and approved `/v1/speech` returned a non-empty `audio/mpeg` payload (`33,496` base64 characters). This is the exact payload the iOS `VoiceOutputService` decodes and plays with `AVAudioPlayer`.
- Phrase-level correction and voice ingestion (2026-10-24): added a narrow Gemini review trigger for phrase-level VSR errors such as `YAHOO IS THIS`, allowing the evidence-preserving correction `YO WHO IS THIS` while rejecting unrelated rewrites. Added consent-gated `POST /v1/voices/clone` forwarding an audio sample to Cartesia's private clone endpoint, an eight-second explicit iOS enrollment flow, local voice-ID reuse for TTS, and the microphone usage disclosure. Modal redeployed; health returned 200 and the clone endpoint correctly rejected missing consent with HTTP 403 without consuming clone credits. Simulator build succeeded; the physical phone became temporarily unavailable during reinstall and needs reconnecting for the updated binary.
- One-shot rebuild attempt (2026-10-26): generic signed iOS build succeeded; simulator build/install/launch succeeded with `com.raahilrussell.voiceback`. Physical install was blocked because the connected iPhone was locked and could not mount the developer disk image. The deployed Modal URL returned HTTP 404 because the Modal workspace is currently disabled; no inference or Cartesia clone request was sent.
- Silent Speech spec reconciliation (2026-10-26): read the newly supplied `SILENT_SPEECH_CODEX_BUILD_SPEC.md` end to end. Added typed `/readyz`, explicit real/demo settings, model registry/limitations/decision/test-report docs, reproducible `make check`, and a regression test proving Gemini cannot turn `YAHOO IS THIS` into an unlisted `YO WHO IS THIS` candidate. Validation: **21 backend tests passed**, Ruff passed, Xcode project listing passed, readiness and candidate-restriction smoke tests passed. The real Modal model gate remains blocked by the disabled workspace; no fake inference result is claimed.
- Local compute transition (2026-10-26): switched the default backend from Modal to the laptop, added a warm in-process local Auto-AVSR adapter with FFmpeg audio stripping, installed the Python 3.11 Apple Silicon runtime, cloned upstream Auto-AVSR, downloaded the ignored 1.0 GB authorized checkpoint, and configured the iOS client for `http://192.168.1.196:8000`. Real local results: `IMG_5966.MOV` returned in 4.034 s and `IMG_5967.MOV` returned in 1.727 s; local HTTP upload returned `THIS IS THE GROUND TRUTH` in 1.421 s with `audio_used=false`. Device reinstall remains blocked only by the locked iPhone developer image.
- Local failure recovery (2026-10-26): reproduced a real Gemini HTTP 503 while local Auto-AVSR itself succeeded. Changed the API to preserve and return the raw visual transcript when the optional Gemini review provider is unavailable; speech approval remains unavailable until review succeeds. Added regression coverage. Validation: **22 backend tests passed**, Ruff passed, Swift unit tests passed, simulator test passed, and the corrected signed app installed on the connected iPhone. Launch still requires the phone to be unlocked.
- Physical iPhone run (2026-10-24): device `RaahiliPhone` identified as iPhone 15 Pro Max, connected; signed `iphoneos` build succeeded with the Apple Development certificate and provisioning profile; app installed successfully. Launch was denied by iOS because the device was locked. Unlocking the phone is the only remaining launch gate for this run.
- Stage 02 signing repair (2026-10-24): project Debug/Release settings now enable Automatic Signing with Personal Team `28N3GP9MWX`. A fresh signed device build completed with the Apple Development certificate and `iOS Team Provisioning Profile: com.raahilrussell.voiceback`; the newly built app **installed and launched** on RaahiliPhone.
- Stage 02 remaining gate (needs user): unlock RaahiliPhone and launch `VoiceBack`; then silently mouth an unseen sentence, confirm the displayed transcript, verify no microphone prompt, and `ffprobe` the recorded clip to show 0 audio streams. Backend + deployed Modal are ready.
- Stage 00 is VERIFIED COMPLETE and committed as `fb59dc6` (backend typed `/health` + `/v1` router + 5 tests; simulator build, `xcodebuild test`, and app launch on iPhone 17 sim).
- Stage 01 progress: upstream Auto-AVSR inspection, real T4 inference, 25 fps normalization, warm-container reuse, FP16 inference, and beam-size comparison are recorded in `docs/INFERENCE_FEASIBILITY.md`.
- Modal validation: authenticated as profile `raahil-32424`; image built and uploaded; official Auto-AVSR checkout and 1 GB official VSR checkpoint cached in `voiceback-model-cache`; T4/CUDA/MediaPipe initialized; audio-stripped video path reached face detection. The available public fixture had no detectable face, so no transcript was claimed.
- Local deploy re-validated 2026-10-24: `modal run inference/modal_app.py` (no GPU) from the repo built the image, uploaded sources, and created both `transcribe_video` and `transcribe_official_demo` functions (run `ap-bMrKSgfv4m3pAp4cKZam7W`). Confirms the app deploys from this machine; produces no transcript.
- Latest accuracy run: ground truth was “this is the ground truth”; outputs were `THEY TEND TO TURN AROUND TRUTH` (7.245 s) and `THIS IS TURN AROUND TO` (2.554 s). Audio was removed and both ran on `cuda:0`; the outputs are not yet accurate enough for speech output.
- Stage 01 environment: macOS (Darwin 25.6.0), Apple Silicon arm64; no NVIDIA GPU; PyTorch, ffmpeg, and ground-truth sample videos not present; network available. Backend runs in the Python 3.14.7 `.venv`.
- Environment: macOS (Darwin 25.6.0); full Xcode **26.6 (Build 17F113)** installed at `/Users/raahil/Downloads/Xcode.app` with iOS **26.5** simulator runtime available; system `xcode-select -p` now points at the full Xcode after administrator approval. Python **3.14.7** in an isolated `.venv` (system Python is PEP 668 externally-managed).

## Stage status

| Stage | Status | Validation | Blockers | Last Commit |
|---|---|---|---|---|
| 00 Foundation | VERIFIED COMPLETE | Backend: 5 tests pass; live `/health` returns HTTP 200. Xcode: project parses, simulator build and `xcodebuild test` succeed, app installs and launches | No Stage 00 blockers; physical-device camera behavior remains future validation | pending commit |
| 01 Visual-only lip-reading | VERIFIED COMPLETE | Best checkpoint `vsr_trlrs2lrs3vox2avsp_base.pth` + 25 fps fix → **0% WER exact-sentence** audio-free transcript on a consented clip (second clip 40%). Real reusable adapter; `audio_used=False` verified; feasibility decision POSITIVE | Per-clip silent/spoken labels + more takes are future refinement, not gate blockers | 121cbf7 |
| 02 iOS recording/VSR | IMPLEMENTED — UNVERIFIED | Backend `POST /v1/transcriptions` (13 tests pass) proven end-to-end against deployed Modal with a real clip (`THIS IS THE GROUND TRUTH`, audio_used=false); iOS simulator build + `xcodebuild test` SUCCEEDED | Physical iPhone + Apple signing + LAN backend URL required to verify real recording/upload/display, no-mic prompt, and 0 audio streams | pending |
| 03 Gemini interpretation | BACKEND VALIDATED | Live structured request selected the correct supplied candidate; `PRO`/`BRO` returned a 0.75 word check and clarification; deterministic fast path and live Modal HTTP 200 verified; 16 backend tests pass | Full phone-path evaluation on multiple ambiguous clips; Pro requires paid quota | pending |
| 04 Clarification/gestures | PARTIALLY IMPLEMENTED | Clarification API resolves yes/no and candidate-number answers; approval remains blocked while uncertain | Physical-device gesture calibration and Vision/ARKit stream remain | pending |
| 05 Cartesia voice/TTS | VERIFIED WITH DEFAULT VOICE | Consent-gated enrollment state, live Cartesia MP3 response, approval-gated TTS endpoint, iOS AVAudioPlayer path, and mocked provider test pass | Replace demo fallback with a personal consented voice when available | d141a8c |
| 06 End-to-end | SOFTWARE COMPLETE — DEVICE PENDING | Video → VSR → Gemini → approval → live Cartesia audio contract verified; 20 backend tests + Xcode test suite pass | Physical iPhone camera/gesture/audio playback test | pending |
| 07 Benchmark/reliability | NOT STARTED | None | Ground truth, repeatable environment | — |
| 08 Demo/GitHub | NOT STARTED | Public repository exists, but final demo is not validated | Final demo must use real verified paths | 3c73e50 |

## Stage 00 task checklist

- [x] Create project inside existing CalHacks workspace without modifying sibling projects.
- [x] Initialize local Git repository and public GitHub remote.
- [x] Create real `ios/VoiceBack.xcodeproj` and SwiftUI source structure.
- [x] Create FastAPI app, typed settings, `/health`, and one backend test.
- [x] Add `.env.example`, local ignored `.env`, and secret/artifact ignore rules.
- [x] Verify full Xcode project parse (`xcodebuild -list` succeeds under Xcode 26.6).
- [x] Verify simulator build succeeds after removing `Info.plist` from Copy Bundle Resources.
- [x] Verify app installs and launches in iPhone 17 simulator (`com.raahilrussell.voiceback`).
- [x] Add typed product API schemas and versioned router tests (`app/schemas/health.py`, `app/api/v1.py`, `tests/test_api_v1.py`, `tests/test_config.py`).
- [x] Commit foundation fix and progress evidence.

## Evidence collected (this session, 2026-10-24)

Backend — isolated environment, install, and tests:

```text
# .venv/bin/python --version
Python 3.14.7

# .venv/bin/python -m pytest backend/tests -v
backend/tests/test_api_v1.py::test_v1_health_returns_typed_payload PASSED
backend/tests/test_api_v1.py::test_v1_health_rejects_unknown_method PASSED
backend/tests/test_config.py::test_settings_defaults PASSED
backend/tests/test_config.py::test_settings_rejects_invalid_port PASSED
backend/tests/test_health.py::test_health_returns_typed_payload PASSED
========================= 5 passed, 1 warning in 0.24s =========================
```

Backend — live server typed responses (uvicorn `app.main:app`, port 8000):

```text
# curl -fsS http://127.0.0.1:8000/health      -> HTTP 200
{"status":"ok","environment":"development","version":"0.1.0"}

# curl -fsS http://127.0.0.1:8000/v1/health   -> HTTP 200
{"status":"ok","environment":"development","version":"0.1.0"}
```

Secret-safety and clean tree:

```text
# git check-ignore -v .env
.gitignore:2:.env	.env
# git check-ignore -v .venv
.gitignore:3:.venv/	.venv
# git diff --check
(no whitespace errors)
# git ls-files | grep -iE '\.env$|\.mp4$|\.pt$|\.ckpt$|DerivedData'  -> none tracked
```

Xcode — toolchain, project parse, duplicate plist fix, build, and launch:

```text
# xcodebuild -version (DEVELOPER_DIR=/Users/raahil/Downloads/Xcode.app/Contents/Developer)
Xcode 26.6
Build version 17F113

# xcrun simctl list runtimes
iOS 26.5 (26.5 - 23F77) - com.apple.CoreSimulator.SimRuntime.iOS-26-5

# xcodebuild -list -project ios/VoiceBack.xcodeproj
Targets: VoiceBack, VoiceBackTests ; Schemes: VoiceBack ; Configs: Debug, Release

# Root cause found in ios/VoiceBack.xcodeproj/project.pbxproj:
# PBXResourcesBuildPhase contained Info.plist while INFOPLIST_FILE also processed it.
# Removed the PBXBuildFile entry and left the file reference + INFOPLIST_FILE intact.

# xcodebuild -project ios/VoiceBack.xcodeproj -scheme VoiceBack \
#   -destination 'platform=iOS Simulator,name=iPhone 17,OS=26.5' \
#   -derivedDataPath /tmp/VoiceBackDerived2 CODE_SIGNING_ALLOWED=NO build
** BUILD SUCCEEDED **

# xcrun simctl install ... /tmp/VoiceBackDerived2/Build/Products/Debug-iphonesimulator/VoiceBack.app
# xcrun simctl launch ... com.voiceback.app
com.voiceback.app: 89845

# latest simulator build after Swift UI fix
# make simulator-build
** BUILD SUCCEEDED **

# xcrun simctl install booted /tmp/VoiceBackDerived/Build/Products/Debug-iphonesimulator/VoiceBack.app
# xcrun simctl launch booted com.raahilrussell.voiceback
com.raahilrussell.voiceback: 758

# .venv/bin/python -m pytest backend/tests -q
13 passed, 1 warning

# xcodebuild ... -scheme VoiceBack -destination 'platform=iOS Simulator,name=iPhone 17,OS=26.5' test
Test Suite 'All tests' passed
Executed 1 test, with 0 failures
** TEST SUCCEEDED **
```

Modal / Auto-AVSR — remote validation:

```text
# modal profile current
raahil-32424

# modal run inference/modal_app.py
voiceback-inference is authenticated and configured for T4 execution.
Modal image built and uploaded with FFmpeg, PyTorch, PyAV, MediaPipe 0.10.21,
and the official Auto-AVSR checkout.

# modal run inference/modal_app.py --demo
Official 1 GB VSR checkpoint downloaded to Modal volume voiceback-model-cache.
CUDA/EGL initialized on Tesla T4; MediaPipe initialized; audio-stripped video
path executed. The public fixture had no detectable face and stopped at the
upstream detector assertion. No transcript was claimed.
```

Root cause: `INFOPLIST_FILE = VoiceBack/Resources/Info.plist` already processes the plist; the same file is additionally listed in the target's Copy Bundle Resources phase (`PBXResourcesBuildPhase`), so two build commands write `VoiceBack.app/Info.plist`.

## Build commands (for re-running after the fix)

```bash
export DEVELOPER_DIR=/Users/raahil/Downloads/Xcode.app/Contents/Developer
cd "/Users/raahil/Desktop/University of Pennsylvania/Freshman Year - 2026-2027/ESE/CalHacks/VoiceBack"
xcodebuild -project ios/VoiceBack.xcodeproj -scheme VoiceBack -sdk iphonesimulator \
  -configuration Debug -derivedDataPath /tmp/VoiceBackDerived CODE_SIGNING_ALLOWED=NO build

# backend
python3 -m venv .venv && .venv/bin/python -m pip install -e 'backend[dev]'
.venv/bin/python -m pytest backend/tests
.venv/bin/python -m uvicorn app.main:app --app-dir backend --port 8000
```

## Unresolved bugs and risks

- Physical-device camera behavior is not yet validated; simulator results never prove real camera behavior.
- Live Cartesia enrollment and physical-device gesture/camera validation remain provider/device gates.
- No physical-device evidence exists; simulator results never prove real camera behavior.
- Camera preview is a UI placeholder; the capture service boundary is not wired to a preview layer.
- Backend provider services intentionally raise `NotImplementedError`.
- No Auto-AVSR checkpoint, GPU environment, or silent-mouthing benchmark exists yet.
- Gemini, Cartesia contract, approval gate, and end-to-end mocked flow are validated; live Cartesia voice enrollment and physical gesture validation remain.

## Decisions made

- Keep provider secrets in backend environment variables only.
- Preserve a video-only recognition path with no microphone input or usage description.
- Foundation API surface exposes only service metadata (`/health`, `/v1/health`); product endpoints are added stage-by-stage, never fabricated.
- Build with `DEVELOPER_DIR` targeting the installed full Xcode rather than changing the global `xcode-select`.
- Use an isolated `.venv` because the system Python is PEP 668 externally-managed.
- Validate visual model feasibility before building extensive downstream UX.
- Require explicit final approval before synthesis; gesture answers are not approval.
- Keep model weights, recordings, generated audio, and build artifacts out of Git.

## Required user actions

- No required Stage 00 user action remains. Approval is required before Stage 01.
- Optional: run `sudo xcode-select -s /Users/raahil/Downloads/Xcode.app/Contents/Developer` to make the full Xcode the default toolchain.
- Provide or authorize a GPU environment and model checkpoint for Stage 01.
- Provide backend Gemini and Cartesia credentials only when those stages begin.
- Provide consented voice/video samples and ground-truth sentences for evaluation.
- Approve advancing from each validation gate.

## Suggested next prompt to Claude

`Continue to Stage 01 only after reviewing the verified Stage 00 evidence. Inspect the official Auto-AVSR repository, requirements, license, checkpoint, and input preprocessing before downloading or integrating anything. Stop at the Stage 01 feasibility gate.`
