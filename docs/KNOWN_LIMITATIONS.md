# Known limitations

- The current Auto-AVSR path is utterance-level, not proven streaming.
- Genuine silent-articulation accuracy is not established for the target user
  population; public speech benchmarks are not product evidence.
- Raw model scores and Gemini confidence fields are not calibrated probabilities.
- The physical camera path requires a real iPhone; simulator validation cannot
  verify camera framing or microphone/privacy prompts.
- Modal availability, GPU capacity, provider quotas, and credentials are
  external runtime dependencies.
