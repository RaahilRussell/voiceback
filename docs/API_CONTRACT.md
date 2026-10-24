# API contract

Initial endpoint: `GET /health`.

Planned endpoints:

- `POST /v1/transcriptions` — visual-only video upload and candidate transcripts
- `POST /v1/clarifications` — ambiguity resolution question and answer
- `POST /v1/voices/enrollment` — consent-based enrollment session
- `POST /v1/speech` — approved text to generated audio

All production endpoints must make approval state explicit and must reject microphone audio inputs.

