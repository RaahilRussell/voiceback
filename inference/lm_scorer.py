"""Tokenizer-safe causal language-model scorer for Auto-AVSR shallow fusion.

Auto-AVSR uses a SentencePiece vocabulary while the optional causal LM uses
its own tokenizer. We map ASR prefixes back to text first, then score the
resulting text continuation with the LM. No token IDs are assumed to match.
The scorer is a partial ESPnet scorer, so it only evaluates Auto-AVSR's
pre-beam token candidates before beam pruning.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

try:
    from espnet.nets.scorer_interface import BatchPartialScorerInterface
except ImportError:  # Keeps lightweight unit tests importable without Auto-AVSR.
    class BatchPartialScorerInterface:  # type: ignore[no-redef]
        pass


def combine_scores(visual_score: float, lm_score: float, lm_weight: float) -> float:
    """Return shallow-fusion score; both inputs are log-score quantities."""

    return visual_score + lm_weight * lm_score


class CausalTextLMScorer(BatchPartialScorerInterface):
    """Lazy Hugging Face causal-LM scorer implementing ESPnet partial scoring."""

    def __init__(
        self,
        token_list: list[str],
        decode_ids: Callable[[list[int]], str],
        model_name: str,
        device: str = "cpu",
    ) -> None:
        self.token_list = token_list
        self.decode_ids = decode_ids
        self.model_name = model_name
        self.device = device
        self._tokenizer = None
        self._model = None
        self.trace: list[dict[str, object]] = []

    def reset_trace(self) -> None:
        self.trace = []

    def _load(self) -> None:
        if self._model is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self._model.to(self.device).eval()

    def init_state(self, _x: Any) -> None:
        return None

    def select_state(self, _state: Any, _i: int, new_id: int | None = None) -> None:
        return None

    def batch_init_state(self, _x: Any) -> list[None]:
        return []

    def batch_score_partial(self, ys, next_tokens, states, xs):
        import torch

        self._load()
        scores = torch.zeros(
            ys.shape[0], len(self.token_list), dtype=xs.dtype, device=xs.device
        )
        for row, (prefix_ids, candidate_ids) in enumerate(zip(ys, next_tokens)):
            prefix = self.decode_ids([int(item) for item in prefix_ids.tolist()[1:]])
            texts = []
            ids = []
            for token_id in candidate_ids.tolist():
                token_text = self.decode_ids([int(token_id)])
                ids.append(token_id)
                texts.append(prefix + token_text)
            values = self._continuation_log_probs(prefix, texts)
            for token_text, token_id, value in zip(texts, ids, values):
                scores[row, token_id] = value
                if len(self.trace) < 256:
                    self.trace.append(
                        {
                            "prefix": prefix,
                            "candidate_token_id": token_id,
                            "candidate_text": token_text,
                            "lm_log_probability": value,
                            "lm_probability": float(torch.exp(torch.tensor(value)).item()),
                        }
                    )
        return scores, [None] * ys.shape[0]

    def _continuation_log_probs(self, prefix: str, continuations: list[str]) -> list[float]:
        """Score text suffixes while handling a tokenizer boundary mismatch.

        If the LM tokenizer does not preserve the prefix token boundary after
        appending an ASR piece, score from the longest common token prefix. This
        avoids pretending that incompatible ASR/LM token IDs are aligned.
        """

        import torch

        assert self._tokenizer is not None and self._model is not None
        prefix_ids = self._tokenizer(prefix, add_special_tokens=False)["input_ids"]
        encoded = self._tokenizer(
            continuations,
            add_special_tokens=False,
            padding=True,
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].to(self._model.device)
        attention = encoded["attention_mask"].to(self._model.device)
        score_first_token = not prefix_ids
        if score_first_token:
            bos_id = self._tokenizer.bos_token_id
            if bos_id is None:
                bos_id = self._tokenizer.eos_token_id
            if bos_id is None:
                raise ValueError("causal LM tokenizer has neither BOS nor EOS token")
            bos = torch.full(
                (input_ids.shape[0], 1), bos_id, dtype=input_ids.dtype, device=input_ids.device
            )
            input_ids = torch.cat((bos, input_ids), dim=1)
            attention = torch.cat(
                (torch.ones_like(attention[:, :1]), attention), dim=1
            )
        with torch.inference_mode():
            logits = self._model(input_ids=input_ids, attention_mask=attention).logits
            log_probs = torch.log_softmax(logits, dim=-1)
        results = []
        for row, full_text in enumerate(continuations):
            full_ids = self._tokenizer(full_text, add_special_tokens=False)["input_ids"]
            common = 0
            for left, right in zip(prefix_ids, full_ids):
                if left != right:
                    break
                common += 1
            total = 0.0
            # Logits[t] predict input_ids[t + 1]. The first token has no
            # preceding token in a decoder-only LM and is intentionally omitted.
            for target_index in range(
                0 if score_first_token else max(1, common), len(full_ids)
            ):
                position = target_index if score_first_token else target_index - 1
                total += float(log_probs[row, position, full_ids[target_index]].item())
            results.append(total)
        return results
