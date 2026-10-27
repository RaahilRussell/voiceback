# Visual-language fusion benchmark

This is the first reproducible decoder-level fusion check. It uses the same
local Auto-AVSR checkpoint and the same clip for both runs; the clip is not a
held-out accuracy set, so these numbers are latency/behavior evidence only.

Command:

```bash
./.venv-local/bin/python - <<'PY'
from inference.model_adapter import ModelAdapter

for weight in (0.0, 0.1):
    result = ModelAdapter(
        checkpoint_path="checkpoints/vsr_trlrs2lrs3vox2avsp_base.pth",
        device="cpu",
        upstream_root=".local/auto_avsr",
        beam_size=5,
        lm_model_name=None if weight == 0 else "distilgpt2",
        lm_fusion_weight=weight,
    ).transcribe_video("../references/IMG_5967.MOV")
    print(weight, result)
PY
```

Observed on 2026-10-27, Apple M3 Pro CPU:

| Configuration | Top transcript | Model time | Wall time | Audio |
| --- | --- | ---: | ---: | --- |
| Auto-AVSR, λ=0 | `AND WE'RE GOING TO TALK A LITTLE BIT ABOUT THAT` | 2.038 s | 7.303 s | false |
| Auto-AVSR + distilgpt2, λ=0.1 | `AND I'M GOING TO GO AHEAD AND` | 5.128 s | 6.416 s | false |

The candidate list and top score changed, proving that the LM score affected
beam expansion rather than only post-processing. The result is not an accuracy
win: the clip has no independent ground-truth label in this benchmark. The
default remains λ=0.0 until a held-out set demonstrates lower WER and acceptable
latency. Gemini remains outside this inner loop and is not called per token.

As a baseline invariant, the custom beam object at λ=0 was also run on the
same encoded feature tensor as Auto-AVSR's original `get_beam_search_decoder`.
The top hypotheses and all 16 returned hypothesis scores matched exactly
(`score_delta = 0.0` for every compared hypothesis).
