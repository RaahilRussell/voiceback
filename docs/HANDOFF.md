# Handoff

This is a clean workspace scaffold for continued development in Xcode and Claude Code. The iOS project is real and opens in Xcode; backend integrations are intentionally represented by typed boundaries. Start with the first vertical slice in `IMPLEMENTATION_PLAN.md`. Never commit `.env`, user video, voice recordings, generated audio, or model checkpoints.

Important design constraint: jaw and face landmarks are intended for cheap crop
alignment, framing quality, and gesture detection. Auto-AVSR should continue to
receive its validated mouth-region input until a multimodal replacement is
trained and benchmarked. Keep the original transcription visible and require
explicit approval before Cartesia speech output.

## Current handoff state — 2026-10-24

- Public repository: `https://github.com/RaahilRussell/voiceback` on `main`.
- Physical-device app bundle: `com.raahilrussell.voiceback`.
- The iPhone build is signed with the active Personal Team and installs/launched
  successfully on RaahiliPhone.
- The phone now posts video to the public Modal endpoint:
  `https://raahil-32424--voiceback-inference-web.us-east.modal.run`.
- The endpoint was verified with a real clip and returned
  `THIS IS THE GROUND TRUTH` with `audio_used=false`.
- Modal is configured with one warm T4 (`min_containers=1`) and a 15-minute
  scale-down window. This consumes GPU credits while deployed; stop the app
  when testing is finished if credit usage matters.
- The endpoint now has a deterministic fast path: a single candidate without a
  known lip-reading collision skips Gemini, while PRO/BRO-style collisions still
  invoke Gemini. A current ground-truth request returned HTTP 200 with the raw
  result and fast-path interpretation. The measured request was still 24.65 s
  because Modal had to wait for T4 capacity; the actual model timing was 7.09 s.
  Reaching a two-second target requires streaming windows or a faster/on-device
  model, and depends on GPU capacity.
- Gemini is wired after raw Auto-AVSR output as one typed
  correction/ranking/clarification call. The live key was validated with
  `gemini-3.1-flash-lite`: structured output returned in 4.73 seconds and
  selected the correct supplied candidate at 0.95 confidence. The client uses
  temperature 0, a fixed seed, one candidate, cached client state, and a 12
  second request deadline. A deliberate `PRO`/`BRO` ambiguity test returned a
  word-level check at 0.75 confidence and blocked approval with a clarification
  question. Cartesia is not wired into the phone flow.
- Gemini Pro models are not usable with the current key's free-tier quota;
  `gemini-3.1-pro-preview` returned quota 0. Keep the model configurable and
  use Flash Lite for the latency-sensitive demo path until paid quota is added.

