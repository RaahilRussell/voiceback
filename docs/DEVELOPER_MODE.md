# Developer diagnostics mode

The local ignored `.env` is currently configured with:

```text
DEVELOPER_MODE=true
LM_MODEL_NAME=distilgpt2
LM_FUSION_WEIGHT=0.1
```

This is intentionally a debug configuration. It makes the transcription
response include:

- the visual beam candidates and raw decoder scores;
- the fusion formula and λ value;
- up to 256 actual LM candidate evaluations, including the mapped text,
  log-probability, and probability;
- whether Gemini was available, invoked, skipped, or failed;
- the exact Gemini request prompt and raw response when it ran.

The iOS result screen shows this under **Developer diagnostics**. Developer
mode forces one Gemini review whenever there is more than one candidate, which
is useful for diagnosing cases such as `GROUND` versus `CROWN`. Normal mode
keeps the selective review policy and should use `LM_FUSION_WEIGHT=0.0` until a
held-out accuracy benchmark supports a higher value.

The endpoint can also be enabled per request with:

```text
X-VoiceBack-Developer-Mode: true
```

Do not commit `.env` or share its diagnostics payload outside the local test
environment: the prompt can contain private transcriptions and context.
