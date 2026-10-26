# VoiceBack

VoiceBack is a native iOS assistive communication app for people who can articulate words with their lips but cannot produce normal audible speech. It combines silent visual speech recognition, context-aware clarification, and consent-based personal voice synthesis.

## Repository layout

- `ios/` — Swift 6 / SwiftUI client and Xcode project
- `backend/` — Python 3.11+ FastAPI service boundary
- `inference/` — adapter boundary for the visual-only Auto-AVSR model
- `docs/` — architecture, API contract, implementation plan, and handoff notes

## Quick start

1. Open `ios/VoiceBack.xcodeproj` in Xcode 16 or newer.
2. Create a Python 3.11+ virtual environment and install the backend package:
   `python3 -m venv .venv && . .venv/bin/activate && pip install -e 'backend[dev]'`
3. Copy `.env.example` to `.env` and add credentials only when integrations are implemented.
4. Run `make test` for the backend checks.

The reproducible checks are `make lint`, `make test`, `make check`, and
`make xcode-list`. `GET /health` reports process liveness; `GET /readyz`
reports model, Gemini, and TTS readiness separately. A missing real model must
remain an explicit blocker; demo fixtures are never reported as real inference.

No microphone audio is used by the visual speech recognition path. Model weights and credentials are intentionally not included.

