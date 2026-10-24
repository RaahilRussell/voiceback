# API contract

Initial endpoint: `GET /health`.

Planned endpoints:

- `POST /v1/transcriptions` — visual-only video upload and candidate transcripts
- `POST /v1/clarifications` — ambiguity resolution question and answer
- `POST /v1/voices/enrollment` — consent-based enrollment session
- `POST /v1/speech` — approved text to generated audio

All production endpoints must make approval state explicit and must reject microphone audio inputs.

## Gemini interpretation contract

Gemini is intentionally one call rather than a separate correction and decision
model. It receives the original Auto-AVSR text, up to five candidates, and
conversation context. Structured output returns the selected candidate,
confidence, and—when confidence is insufficient—a short clarification question.

The result is a proposal only. The backend must preserve `original_text`, must
not speak `corrected_text` automatically, and must require an explicit user
approval event before calling Cartesia.

