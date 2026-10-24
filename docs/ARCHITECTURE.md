# Architecture

The iOS client captures front-camera video only. A lightweight local landmark
pipeline uses face, mouth, and jaw landmarks for crop stabilization, head-pose
quality checks, and gesture signals. It does not require microphone audio.

The visual-speech path remains deliberately separated from the gesture path:

- Auto-AVSR receives a normalized, stabilized mouth crop and performs visual
  speech recognition.
- Vision/ARKit produces head nod, head shake, jaw-motion, and framing-quality
  metadata locally.
- Jaw and head landmarks are not appended to the Auto-AVSR input unless a
  future multimodal model is trained and validated for that input format.

The backend produces the original transcription and candidate text. Gemini may
propose context-aware corrections, but it cannot silently replace the original
or trigger speech. The clarification engine uses candidate uncertainty and the
local gesture/accessibility signals to ask a short question. Cartesia is called
only after explicit user approval and consent checks, and only for the approved
sentence.

The system should measure landmark preprocessing, video normalization, model
loading, warm inference, Gemini, Cartesia, and playback as separate latency
components. This prevents expensive GPU inference from being confused with
cheap alignment or gesture preprocessing.

