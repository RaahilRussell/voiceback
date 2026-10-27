# Known limitations

- The current Auto-AVSR path is utterance-level, not proven causal streaming.
  The live WebSocket now transports JPEG frames and can show an explicitly
  labeled `repeated_offline_prefix` preview, but that reruns the offline model
  on growing prefixes and is not cached next-token decoding.
- Genuine silent-articulation accuracy is not established for the target user
  population; public speech benchmarks are not product evidence.
- Raw model scores and Gemini confidence fields are not calibrated probabilities.
- Optional shallow fusion now injects a local causal-LM score into Auto-AVSR's
  `BatchBeamSearch` before beam pruning. It is genuine decoder-level fusion,
  but the default lambda remains `0.0`: `distilgpt2` is a generic English LM,
  not a silent-speech LM, and the first real clip benchmark changed the result
  while adding about five seconds of cold local CPU time. A task-specific LM,
  KV-cache reuse, and held-out tuning are still required before enabling it.
- The LM scorer maps Auto-AVSR text prefixes into the LM tokenizer and scores
  only the candidate continuations selected by Auto-AVSR's pre-beam. This is
  correct across tokenizer boundaries but not yet an optimized incremental KV
  cache implementation.
- No trained P/B/M or F/V specialist weights exist. The specialist extension
  point returns an explicit `unavailable` result and never fabricates evidence.
- The physical camera path requires a real iPhone; simulator validation cannot
  verify camera framing or microphone/privacy prompts.
- Modal availability, GPU capacity, provider quotas, and credentials are
  external runtime dependencies.
