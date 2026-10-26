# Model registry

| Component | State | Provenance | Notes |
|---|---|---|---|
| Auto-AVSR visual-only adapter | integrated, externally cached | `mpc001/auto_avsr`; checkpoint details in `INFERENCE_FEASIBILITY.md` | Audio is stripped before inference; weights are not committed. |
| VALLR-style phoneme branch | not integrated | research reference only | Licensing and deployability are not established. |
| Gemini | optional server-side | configured model is environment-controlled | Candidate-restricted structured output; not calibrated confidence. |
| Cartesia | optional server-side | provider API | Only approved text is synthesized. |
