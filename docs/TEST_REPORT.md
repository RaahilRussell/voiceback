# Test report

## 2026-10-26 Phase 0/1 reconciliation

- Backend: `make test` — **21 passed**, one Starlette deprecation warning.
- Static checks: `make lint` — **passed**.
- Project parse: `make xcode-list` — **passed**, VoiceBack and VoiceBackTests targets and the shared VoiceBack scheme found.
- Readiness smoke: `GET /readyz` — **HTTP 200**, reports `mode=real`, Gemini/TTS readiness, and `generalist_ready=true` for the local checkpoint.
- Candidate restriction smoke: an attempted `YAHOO IS THIS` → `YO WHO IS THIS` rewrite was rejected and converted to re-mouth/type clarification.
- Xcode: simulator build/install/launch previously succeeded; the latest
  physical install attempt was blocked by a locked iPhone developer disk
  image.
- Modal: currently externally disabled; no new GPU or provider call is claimed.
- Local laptop: Apple Silicon M3 Pro, Python 3.11 environment, MPS available
  but CPU selected because the upstream beam decoder has an MPS tensor mismatch.
  The real checkpoint loaded locally; both authorized reference clips produced
  audio-free transcripts. The local HTTP endpoint returned `THIS IS THE GROUND
  TRUTH` for `IMG_5967.MOV` in 1.421 seconds with `audio_used=false`.
- Gemini outage recovery: a live local request reproduced Gemini HTTP 503
  (`UNAVAILABLE`/high demand) after successful visual inference. The endpoint
  now returns the raw transcript with no interpretation instead of HTTP 502;
  the iOS approval gate remains closed. Regression test included.
- Device validation: signed build succeeded and installed on `RaahiliPhone`;
  launch was denied only because iOS reported the device locked.
- Beam/context routing: a real local clip returned five Auto-AVSR hypotheses
  with raw `beam_log_score` values; selective-review unit tests cover known
  PRO/BRO confusion, low-margin disagreement, and high-margin bypass.

This file records observed results only; a pending line is not a pass.
