# VoiceBack agent guidance

- Preserve the silent-input requirement: do not add microphone capture to visual speech recognition.
- Keep uncertain interpretations behind explicit user approval before synthesis.
- Treat voice enrollment as consent-based and never commit credentials, recordings, model weights, or generated audio.
- Keep iOS code compiling with Swift 6 and backend code typed and tested.
- Update `docs/` when API or architecture decisions change.

