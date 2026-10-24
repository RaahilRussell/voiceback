# VoiceBack progress

Last updated: 2026-10-24

## Current state

- Current active stage: **STAGE 01 — Get real silent lip-reading working** (IN PROGRESS → BLOCKED on user-provided inputs; see below).
- Stage 00 is VERIFIED COMPLETE and committed as `fb59dc6` (backend typed `/health` + `/v1` router + 5 tests; simulator build, `xcodebuild test`, and app launch on iPhone 17 sim).
- Stage 01 progress: upstream Auto-AVSR inspection complete and recorded in `docs/INFERENCE_FEASIBILITY.md`; `inference/README.md` updated with verified facts. Real inference is blocked pending inputs only the user can provide.
- Modal prerequisite: authenticated as profile `raahil-32424`; the `voiceback-inference` app definition was accepted by Modal and an ephemeral validation app was created. No GPU inference has been invoked.
- Next action: user provides the three Stage 01 inputs (labeled samples incl. genuine silent mouthing + consent; compute target; install/download authorization); then read `preparation/` for exact preprocessing, run upstream inference, verify the audio-free path, wrap `ModelAdapter`, and measure WER on both conditions.
- Stage 01 environment: macOS (Darwin 25.6.0), Apple Silicon arm64; no NVIDIA GPU; PyTorch, ffmpeg, and ground-truth sample videos not present; network available. Backend runs in the Python 3.14.7 `.venv`.
- Environment: macOS (Darwin 25.6.0); full Xcode **26.6 (Build 17F113)** installed at `/Users/raahil/Downloads/Xcode.app` with iOS **26.5** simulator runtime available; `xcode-select -p` still points at `/Library/Developer/CommandLineTools`, so builds are run with `DEVELOPER_DIR` pointed at the full Xcode. Python **3.14.7** in an isolated `.venv` (system Python is PEP 668 externally-managed).

## Stage status

| Stage | Status | Validation | Blockers | Last Commit |
|---|---|---|---|---|
| 00 Foundation | VERIFIED COMPLETE | Backend: 5 tests pass; live `/health` returns HTTP 200. Xcode: project parses, simulator build and `xcodebuild test` succeed, app installs and launches | No Stage 00 blockers; physical-device camera behavior remains future validation | pending commit |
| 01 Visual-only lip-reading | BLOCKED | Upstream repo/license/architecture/checkpoints/deps/inference-command inspected and recorded in docs/INFERENCE_FEASIBILITY.md | Needs user-provided labeled sample videos (incl. genuine silent mouthing + consent), a compute target (CPU/MPS/remote CUDA), and authorization to install torch/ffmpeg + download a checkpoint | fb59dc6 |
| 02 iOS recording/VSR | NOT STARTED | None | Depends on Stage 01 adapter and physical iPhone | — |
| 03 Gemini interpretation | NOT STARTED | None | Backend key and evaluation set | — |
| 04 Clarification/gestures | NOT STARTED | None | Depends on ambiguity data and physical device | — |
| 05 Cartesia voice/TTS | NOT STARTED | None | Consent, provider access, secure storage | — |
| 06 End-to-end | NOT STARTED | None | Depends on Stages 00–05 | — |
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
- [x] Verify app installs and launches in iPhone 17 simulator (`com.voiceback.app`).
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

# xcodebuild ... -scheme VoiceBack -destination 'platform=iOS Simulator,name=iPhone 17,OS=26.5' test
Test Suite 'All tests' passed
Executed 1 test, with 0 failures
** TEST SUCCEEDED **
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
- Provider integrations, visual model inference, and product flow remain planned later stages.
- No physical-device evidence exists; simulator results never prove real camera behavior.
- Camera preview is a UI placeholder; the capture service boundary is not wired to a preview layer.
- Backend provider services intentionally raise `NotImplementedError`.
- No Auto-AVSR checkpoint, GPU environment, or silent-mouthing benchmark exists yet.
- No Gemini, Cartesia, gesture, privacy, or end-to-end validation exists yet.

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
