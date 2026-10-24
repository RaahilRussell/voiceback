# VoiceBack agent guidance

Read `PROJECT_CONTEXT.md`, `BUILD_WORKFLOW.md`, and `PROGRESS.md` before changing code. Identify the one active stage in `PROGRESS.md`, inspect the real source, and work only on that stage or a prerequisite fix.

Follow this loop: **IMPLEMENT → RUN → OBSERVE → VERIFY → DOCUMENT → NEXT STAGE**. Run the specified tests, record exact evidence and limitations in `PROGRESS.md`, update architecture docs when decisions change, and stop at the validation gate for user approval.

- Preserve the silent-input requirement: visual speech recognition must not capture or consume microphone audio.
- Do not treat Gemini as a lip-reading model or replace failing inference with fabricated output.
- Keep uncertain interpretations behind explicit user approval before synthesis.
- Process head gestures only during active clarification; provide touch fallback and never infer final approval from a gesture.
- Treat voice enrollment as consent-based; never commit credentials, recordings, model weights, generated audio, or build artifacts.
- Keep iOS code Swift 6-compatible and backend code typed and tested.
- Never claim simulator, checkpoint-loading, provider-call, or paper-benchmark evidence proves physical behavior or accuracy.

