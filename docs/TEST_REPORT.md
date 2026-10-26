# Test report

## 2026-10-26 Phase 0/1 reconciliation

- Backend: `make test` — **21 passed**, one Starlette deprecation warning.
- Static checks: `make lint` — **passed**.
- Project parse: `make xcode-list` — **passed**, VoiceBack and VoiceBackTests targets and the shared VoiceBack scheme found.
- Readiness smoke: `GET /readyz` — **HTTP 200**, reports `mode=real`, Gemini/TTS readiness, and local model-not-configured reason.
- Candidate restriction smoke: an attempted `YAHOO IS THIS` → `YO WHO IS THIS` rewrite was rejected and converted to re-mouth/type clarification.
- Xcode: simulator build/install/launch previously succeeded; the latest
  physical install attempt was blocked by a locked iPhone developer disk
  image.
- Modal: currently externally disabled; no new GPU or provider call is claimed.

This file records observed results only; a pending line is not a pass.
