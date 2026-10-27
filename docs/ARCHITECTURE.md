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

The Auto-AVSR decoder now has an optional shallow-fusion path. At each beam
expansion, the visual decoder score is combined with a causal text-LM score:
`visual + lambda * language`. Auto-AVSR's SentencePiece text is decoded back to
text before scoring, so the two tokenizers are never assumed to share IDs. The
language model is only evaluated for the decoder's pre-beam token candidates;
it is not a completed-sentence reranker. The default lambda is zero until a
task-specific benchmark selects a useful value.

The backend still produces the original transcription and candidate text.
Gemini remains an optional outer contextual verifier for ambiguity, supplied
candidate ranking, and conversation context. It cannot silently replace the
visual/fused output or trigger speech. Cartesia is called only after explicit
user approval and consent checks, and only for the approved sentence.

The system should measure landmark preprocessing, video normalization, model
loading, warm inference, Gemini, Cartesia, and playback as separate latency
components. This prevents expensive GPU inference from being confused with
cheap alignment or gesture preprocessing.

