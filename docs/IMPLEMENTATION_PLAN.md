# Implementation plan

## Stage 00 — Foundation

1. Keep the Xcode project building and preserve the no-microphone product
   constraint.
2. Keep backend contracts typed and reject requests that contain microphone
   audio.

## Stage 01 — Camera and visual preprocessing

3. Add a front-camera preview and video capture using AVFoundation.
4. Add a lightweight Vision/ARKit face-landmark pipeline. Use mouth and jaw
   landmarks to stabilize the face, normalize the mouth crop, detect poor
   framing, and provide quality metadata. This is preprocessing and alignment;
   do not pass jaw coordinates into Auto-AVSR unless a compatible model is
   trained for them.
5. Keep Auto-AVSR mouth-focused. Normalize captured video to its required frame
   rate and crop convention before GPU inference. Measure preprocessing time
   separately from model time so optimization effort targets the real cost.
6. Add local head-pose and jaw-motion signals as a separate gesture stream for
   nod, shake, confirmation, and rejection. Never use jaw motion alone to infer
   spoken words.
7. Add accessible on-screen yes/no and candidate-selection controls as a
   fallback when gesture confidence is low.

## Stage 02 — Inference and interpretation

8. Implement upload/session API contracts and FFmpeg normalization.
9. Connect Auto-AVSR through `inference/model_adapter.py` on a configurable GPU,
   preserving audio-free inference, warm model reuse, and explicit timing.
10. Preserve the original Auto-AVSR transcription and alternatives. Send them,
    along with conversation context and gesture/quality metadata, to one Gemini
    structured-output call that performs correction, candidate ranking,
    confidence scoring, and clarification selection together.
11. Add a clarification state machine around Gemini's typed result. Ask a short
    yes/no question when confidence or candidate agreement is low. Require
    explicit user approval before any corrected sentence is spoken.

## Stage 03 — Voice output and privacy

12. Add Cartesia enrollment with explicit consent, secure voice-token handling,
    and deletion/re-enrollment controls.
13. Synthesize only the approved sentence and play it through the iOS audio
    playback path.
14. Add privacy, accessibility, integration, and end-to-end tests, including
    tests proving microphone audio is never required or uploaded.

## Accuracy and performance gates

- Alignment quality must be logged independently from transcription quality.
- Compare mouth-only Auto-AVSR against alignment improvements using labeled clips.
- Track preprocessing time, model load time, warm inference time, and total
  round-trip latency separately.
- Do not mark visual speech recognition complete until outputs are evaluated
  against independent ground truth and uncertain text is blocked from speech.

