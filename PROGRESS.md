# VoiceBack progress

Last updated: 2026-10-24

## Current state

- Current active stage: **STAGE 00 — Repository, Xcode and backend foundation**
- Last verified milestone: repository and backend health test scaffolded; `python3 -m pytest backend/tests` passed (`1 passed`)
- Next action: install/select a full Xcode installation, validate the Xcode project with simulator build, then add typed HTTP schemas/router coverage.
- Current head at workflow start: `79e66f3` (`Initialize VoiceBack monorepo`)
- Environment: macOS; Python 3.14.2 is installed, while the project targets Python 3.11+; full Xcode was not selected/available during initial setup.

## Stage status

| Stage | Status | Validation | Blockers | Last Commit |
|---|---|---|---|---|
| 00 Foundation | IN PROGRESS | Backend health test passed; Xcode build not yet verified | Full Xcode/simulator validation pending; typed product schemas pending | 79e66f3 |
| 01 Visual-only lip-reading | NOT STARTED | None | GPU, model repo/checkpoint, fixtures, feasibility experiment | — |
| 02 iOS recording/VSR | NOT STARTED | None | Depends on Stage 01 adapter and physical iPhone | — |
| 03 Gemini interpretation | NOT STARTED | None | Backend key and evaluation set | — |
| 04 Clarification/gestures | NOT STARTED | None | Depends on ambiguity data and physical device | — |
| 05 Cartesia voice/TTS | NOT STARTED | None | Consent, provider access, secure storage | — |
| 06 End-to-end | NOT STARTED | None | Depends on Stages 00–05 | — |
| 07 Benchmark/reliability | NOT STARTED | None | Ground truth, repeatable environment | — |
| 08 Demo/GitHub | NOT STARTED | Public repository exists, but final demo is not validated | Final demo must use real verified paths | 79e66f3 |

## Stage 00 task checklist

- [x] Create project inside existing CalHacks workspace without modifying sibling projects.
- [x] Initialize local Git repository and public GitHub remote.
- [x] Create real `ios/VoiceBack.xcodeproj` and SwiftUI source structure.
- [x] Create FastAPI app, typed settings, `/health`, and one backend test.
- [x] Add `.env.example`, local ignored `.env`, and secret/artifact ignore rules.
- [ ] Verify full Xcode project parse and simulator build.
- [ ] Verify app launch in simulator.
- [ ] Add typed product API schemas and versioned router tests.
- [ ] Commit this workflow documentation.

Evidence already collected:

```text
python3 -m pytest backend/tests
1 passed

gh repo view RaahilRussell/voiceback
public: true
url: https://github.com/RaahilRussell/voiceback

git check-ignore -v .env
.gitignore:2:.env .env
```

The initial native build attempt was not completed because the machine selected `/Library/Developer/CommandLineTools` and no full Xcode installation was available at that time. This is an environmental blocker, not a passing build result.

## Unresolved bugs and risks

- The hand-authored Xcode project has not yet been parsed/built by full Xcode.
- Camera preview is a UI placeholder; the capture service boundary is not wired to a preview layer.
- Backend provider services intentionally raise `NotImplementedError`.
- No Auto-AVSR checkpoint, GPU environment, or silent-mouthing benchmark exists yet.
- No physical-device, Gemini, Cartesia, gesture, privacy, or end-to-end validation exists yet.

## Decisions made

- Keep provider secrets in backend environment variables only.
- Preserve a video-only recognition path with no microphone input or usage description.
- Validate visual model feasibility before building extensive downstream UX.
- Require explicit final approval before synthesis; gesture answers are not approval.
- Keep model weights, recordings, generated audio, and build artifacts out of Git.

## Required user actions

- Install/select full Xcode and an iOS simulator runtime.
- Provide or authorize a GPU environment and model checkpoint for Stage 01.
- Provide backend Gemini and Cartesia credentials only when those stages begin.
- Provide consented voice/video samples and ground-truth sentences for evaluation.
- Approve advancing from each validation gate.

## Suggested next prompt to Claude

`Continue Stage 00 only. Inspect the current VoiceBack repository, install/select full Xcode if available, validate the real Xcode project with a simulator build, then add typed FastAPI schemas/router tests. Run all Stage 00 validation, update PROGRESS.md with exact evidence, and stop at the gate without starting Stage 01.`

