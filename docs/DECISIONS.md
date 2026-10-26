# Decisions

## 2026-10-26 — Candidate-restricted interpretation

Gemini may rank or abstain among Auto-AVSR candidates, but cannot silently
rewrite a candidate into a fluent sentence. If the intended phrase is absent,
VoiceBack requests a re-mouth, clarification, or type-to-speak fallback.

## 2026-10-26 — Real/demo separation

`DEMO_MODE` is explicit and must be visible in readiness and prediction
contracts. `REAL_MODEL=true` never falls back to synthetic recognition.
