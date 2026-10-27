# Handoff

This is a clean workspace scaffold for continued development in Xcode and Claude Code. The iOS project is real and opens in Xcode; backend integrations are intentionally represented by typed boundaries. Start with the first vertical slice in `IMPLEMENTATION_PLAN.md`. Never commit `.env`, user video, voice recordings, generated audio, or model checkpoints.

Important design constraint: jaw and face landmarks are intended for cheap crop
alignment, framing quality, and gesture detection. Auto-AVSR should continue to
receive its validated mouth-region input until a multimodal replacement is
trained and benchmarked. Keep the original transcription visible and require
explicit approval before Cartesia speech output.

## Current handoff state — 2026-10-27

- Public repository: `https://github.com/RaahilRussell/voiceback` on `main`.
- Physical-device app bundle: `com.raahilrussell.voiceback`.
- The iPhone build is signed with the active Personal Team and installs/launched
  successfully on RaahiliPhone.
- The active development path is now the local laptop backend at
  `http://192.168.1.196:8000`; the iOS client is configured for this LAN URL.
- Modal is retained only as an optional historical/remote adapter and is not
  required for local inference.
- The endpoint was verified with a real clip and returned
  `THIS IS THE GROUND TRUTH` with `audio_used=false`.
- The iOS app now exposes **Start live silent stream**. It sends binary JPEG
  camera frames over `WS /v1/sessions/{session_id}/stream`; the backend emits
  typed capture, provisional-prefix, final-candidate, Gemini-context, and
  approval-decision events. Provisional text is explicitly marked
  `repeated_offline_prefix` because the installed Auto-AVSR checkpoint does
  not yet support cached causal next-token decoding.
- The local runtime keeps one Auto-AVSR adapter warm inside the laptop backend.
  Modal remains available only as a historical/optional remote adapter and is
  not needed for the current development path.
- The endpoint now has a deterministic fast path: a single candidate without a
  known lip-reading collision skips Gemini, while PRO/BRO-style collisions still
  invoke Gemini. A current ground-truth request returned HTTP 200 with the raw
  result and fast-path interpretation. The measured request was still 24.65 s
  because Modal had to wait for T4 capacity; the actual model timing was 7.09 s.
  The warm L4 benchmark reduced model time to 2.80 s and total request time to
  7.08 s. Reaching a two-second total target still requires streaming windows,
  smaller uploads, or a faster/on-device model, and depends on GPU capacity.
- Gemini is wired after raw Auto-AVSR output as one typed
  correction/ranking/clarification call. The live key was validated with
  `gemini-3.1-flash-lite`: structured output returned in 4.73 seconds and
  selected the correct supplied candidate at 0.95 confidence. The client uses
  temperature 0, a fixed seed, one candidate, cached client state, and a 12
  second request deadline. A deliberate `PRO`/`BRO` ambiguity test returned a
  word-level check at 0.75 confidence and blocked approval with a clarification
  question. Cartesia remains a separate remote provider call after approval.
- Gemini Pro models are not usable with the current key's free-tier quota;
  `gemini-3.1-pro-preview` returned quota 0. Keep the model configurable and
  use Flash Lite for the latency-sensitive demo path until paid quota is added.
- Optional visual-language shallow fusion is now wired into the actual
  Auto-AVSR `BatchBeamSearch` insertion point. Configure `LM_MODEL_NAME` and
  `LM_FUSION_WEIGHT`; the shipped `.env` keeps the weight at zero pending a
  held-out accuracy benchmark. See `docs/FUSION_BENCHMARK.md` for the first
  real-clip comparison and its measured tradeoff.
- A typed specialist interface exists for P/B/M, F/V, and other viseme groups,
  but returns `unavailable` until trained weights are supplied. No specialist
  prediction is being claimed.

