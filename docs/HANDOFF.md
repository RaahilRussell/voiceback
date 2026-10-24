# Handoff

This is a clean workspace scaffold for continued development in Xcode and Claude Code. The iOS project is real and opens in Xcode; backend integrations are intentionally represented by typed boundaries. Start with the first vertical slice in `IMPLEMENTATION_PLAN.md`. Never commit `.env`, user video, voice recordings, generated audio, or model checkpoints.

Important design constraint: jaw and face landmarks are intended for cheap crop
alignment, framing quality, and gesture detection. Auto-AVSR should continue to
receive its validated mouth-region input until a multimodal replacement is
trained and benchmarked. Keep the original transcription visible and require
explicit approval before Cartesia speech output.

