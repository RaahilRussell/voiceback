# VoiceBack project context

This document describes what VoiceBack is, how it is structured, and what is real versus planned. The authoritative implementation sequence is in [BUILD_WORKFLOW.md](BUILD_WORKFLOW.md); the current evidence-backed state is in [PROGRESS.md](PROGRESS.md).

## Mission and users

VoiceBack is a native iOS assistive communication application for people who can articulate words with their lips but cannot produce ordinary audible speech. The user silently mouths a sentence at the front-facing iPhone camera. A visual-only speech model proposes text, Gemini helps resolve context-dependent ambiguity, and the user confirms the final sentence before Cartesia synthesizes it in a consent-based personal voice.

The recognition path must not depend on microphone audio. The product must work for users who may have limited or unreliable head control, so head gestures are an optional input with accessible touch controls as a first-class fallback.

## Example journey

1. The user opens VoiceBack and grants camera permission only.
2. The app previews the front camera and records a short silent utterance.
3. The video is normalized and sent to the backend; no microphone track is captured or required.
4. Auto-AVSR or a verified compatible visual-only model returns raw text and available hypotheses.
5. Gemini receives only the evidence and approved context, then returns a structured interpretation and uncertainty.
6. If needed, VoiceBack asks a short grounded yes/no question. The user answers by a calibrated nod/shake or on-screen control.
7. The app shows original transcription, corrected interpretation, and a final approval action.
8. Only after explicit approval does the backend request Cartesia audio, which is played on the iPhone.

## Architecture and data flow

```text
iPhone front camera (video only)
        -> face/mouth tracking and short video capture
        -> URLSession upload
        -> FastAPI validation and FFmpeg normalization
        -> Auto-AVSR visual-only inference on configured GPU
        -> raw transcript + candidates
        -> Gemini structured interpretation
        -> clarification state machine (if uncertain)
        -> explicit user confirmation
        -> Cartesia voice synthesis (backend only)
        -> audio bytes / playback on iPhone
```

The backend owns provider credentials and provider calls. The iOS app never contains Gemini or Cartesia secrets. Video, voice samples, and generated audio are sensitive data and must have a documented retention policy before production use.

## iOS architecture

- `ios/VoiceBack.xcodeproj` is the real Xcode project.
- `ios/VoiceBack/App/VoiceBackApp.swift` is the SwiftUI entry point.
- `ios/VoiceBack/Views/` contains presentation views and camera/transcription UI.
- `ios/VoiceBack/ViewModels/` owns observable screen state.
- `ios/VoiceBack/Services/` owns camera, URLSession, gesture, and audio boundaries.
- `ios/VoiceBack/Models/` contains Codable API/domain models.
- `ios/VoiceBack/Components/` contains reusable approval and accessibility components.
- `ios/VoiceBack/Resources/Info.plist` declares camera usage text; there is intentionally no microphone usage key.

Planned state machine:

`READY -> RECORDING -> VIDEO_UPLOAD -> VISUAL_DECODING -> GEMINI_INTERPRETATION -> CLARIFICATION_IF_NEEDED -> USER_CONFIRMATION -> CARTESIA_SYNTHESIS -> AUDIO_PLAYBACK -> READY`

Every failure and cancellation path must return to a visible recoverable state. Materially uncertain text must not reach synthesis without approval.

## Backend architecture

- `backend/app/main.py` — FastAPI application and health endpoint.
- `backend/app/config.py` — typed environment configuration.
- `backend/app/api/` — planned HTTP routers.
- `backend/app/schemas/` — planned Pydantic request/response models.
- `backend/app/services/video_preprocessor.py` — FFmpeg normalization boundary.
- `backend/app/services/visual_speech_model.py` — visual-only inference boundary.
- `backend/app/services/gemini_client.py` — Gemini boundary.
- `backend/app/services/clarification_engine.py` — candidate/question logic.
- `backend/app/services/cartesia_client.py` — Cartesia boundary.
- `backend/app/services/voice_manager.py` — consent and voice lifecycle.
- `backend/tests/` — backend tests.

The current `/health` endpoint is implemented. Product endpoints are planned in [API_CONTRACT.md](docs/API_CONTRACT.md) and must be added stage-by-stage.

## Model choices and feasibility risks

The initial model target is the official visual-only Auto-AVSR implementation and compatible checkpoint. The agent must inspect its official repository, license, requirements, input preprocessing, and checkpoint before integration. A loaded checkpoint is not evidence of useful lip-reading.

The highest-risk feasibility question is genuinely silent mouthing. Ordinary speech video with audio removed is not equivalent to a person who never produced audio. Stage 01 must measure both conditions, report word error rate and examples, and stop at a feasibility checkpoint if genuine silent articulation is not useful. Gemini cannot replace visual speech recognition or manufacture evidence.

Inference should support a configurable CPU/CUDA/remote-GPU environment. Model weights and large artifacts are not committed.

## Clarification and gesture design

Gemini may propose a correction only from raw model evidence, candidates, decoder scores when actually available, confirmed history, and approved context. It must return structured text plus ambiguity information; self-reported confidence is not treated as calibrated probability.

Clarification questions must be grounded in real candidate differences. Head gestures are processed only while a clarification is active, calibrated per user, temporally smoothed, and rejected when neutral or uncertain. A touch yes/no control must always be available. No gesture may itself count as final speech approval; final approval is explicit.

## Cartesia enrollment and privacy

Voice enrollment requires informed consent, valid sample validation, secure provider reference storage, and deletion support where offered. Cartesia calls occur only through the backend. The generated request must contain only user-approved text. If no enrolled voice exists, a clearly labeled standard synthetic voice may be used as a fallback. The product must not claim perfect historical voice reconstruction.

Credentials are loaded from `.env` locally and `.env.example` documents names only. `.env`, recordings, weights, build output, and generated audio are ignored by Git.

## Repository and current implementation

```text
VoiceBack/
├── ios/VoiceBack.xcodeproj
├── ios/VoiceBack/{App,Views,ViewModels,Services,Models,Components,Resources}
├── ios/VoiceBackTests/
├── backend/app/{api,services,schemas}
├── backend/tests/
├── inference/
├── docs/
├── scripts/
├── .env.example
├── AGENTS.md
├── CLAUDE.md
├── BUILD_WORKFLOW.md
├── PROJECT_CONTEXT.md
└── PROGRESS.md
```

Implemented now: repository, public GitHub remote, real Xcode project files, SwiftUI shell, video-only camera service boundary, approval/transcription model, FastAPI app, typed settings, `/health`, one backend health test, inference/provider service boundaries, and documentation scaffold.

Not implemented: real camera preview session wiring, recording/upload, backend routers and schemas, FFmpeg, Auto-AVSR weights/inference, Gemini calls, gesture tracking, Cartesia enrollment/TTS, end-to-end state machine, benchmark suite, and physical-device validation.

## External references to verify before use

Do not copy assumptions from a stale README. Before Stage 01, inspect the official Auto-AVSR repository and checkpoint/license documentation selected by the implementer. Before provider integration, inspect the current official Google GenAI and Cartesia SDK/API documentation and record the versions in the project. Provider SDK availability and model names can change.

