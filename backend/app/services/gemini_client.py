"""Single-call Gemini correction, ranking, confidence, and clarification."""

from __future__ import annotations

import asyncio
import json
import re
from functools import lru_cache

from app.schemas.interpretation import WORD_CONFIDENCE_THRESHOLD, InterpretationResult

_VISUAL_CONFUSION_GROUPS = (
    frozenset({"pro", "bro"}), frozenset({"pat", "bat"}),
    frozenset({"map", "nap"}), frozenset({"fan", "van"}),
    frozenset({"fine", "vine"}), frozenset({"two", "do"}),
    frozenset({"to", "do"}), frozenset({"tin", "din"}),
    frozenset({"ten", "den"}), frozenset({"meet", "neat"}),
)


@lru_cache(maxsize=1)
def get_gemini_client() -> GeminiClient:
    """Build the configured Gemini boundary for dependency injection."""

    from app.config import settings

    return GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


class GeminiClient:
    def __init__(self, api_key: str | None, model: str = "gemini-3.1-flash-lite") -> None:
        self.api_key = api_key
        self.model = model
        self._client = None

    async def interpret(
        self,
        original_text: str,
        candidates: list[str],
        context: str = "",
        candidate_scores: list[dict] | None = None,
    ) -> InterpretationResult:
        """Return one typed decision; never authorize speech by itself."""

        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for interpretation")
        if not candidates:
            raise ValueError("at least one transcription candidate is required")

        normalized_candidates = list(
            dict.fromkeys(candidate.strip() for candidate in candidates if candidate.strip())
        )[:5]
        if not normalized_candidates:
            raise ValueError("at least one non-empty transcription candidate is required")
        return await asyncio.to_thread(
            self._interpret_sync,
            original_text.strip(),
            normalized_candidates,
            context.strip(),
            candidate_scores,
        )

    @staticmethod
    def should_review(
        original_text: str,
        candidates: list[str],
        candidate_scores: list[dict] | None = None,
    ) -> bool:
        """Route only disagreements or known visual-confusion cases to Gemini."""
        normalized = [candidate.strip().casefold() for candidate in candidates if candidate.strip()]
        if len(set(normalized)) <= 1:
            return False
        original_words = re.findall(r"[a-z']+", original_text.casefold())
        candidate_words = [re.findall(r"[a-z']+", candidate) for candidate in normalized]
        for index, word in enumerate(original_words):
            alternatives = {words[index] for words in candidate_words if index < len(words)}
            if any(
                frozenset({word, alternative}) <= group
                for group in _VISUAL_CONFUSION_GROUPS
                for alternative in alternatives
            ):
                return True
        if candidate_scores and len(candidate_scores) >= 2:
            try:
                margin = float(candidate_scores[0]["raw_score"]) - float(candidate_scores[1]["raw_score"])
                return margin <= 1.0
            except (KeyError, TypeError, ValueError):
                return True
        return True

    def _interpret_sync(
        self,
        original_text: str,
        candidates: list[str],
        context: str,
        candidate_scores: list[dict] | None,
    ) -> InterpretationResult:
        from google import genai
        from google.genai import types

        if self._client is None:
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(
                    timeout=12_000,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            )
        prompt = (
            "You are a conservative visual-speech verifier. Return exactly one JSON decision. "
            "Choose only among the supplied candidate sentences; never invent, rewrite, or "
            "combine words. Do not treat confidence as a calibrated probability. Only add a "
            "word_check for a supplied-candidate word disagreement when the surrounding "
            "sentence context helps rank the alternatives. Use the prefix and suffix context "
            "to estimate which supplied word is more likely next. Never invent an alternative "
            "outside the supplied candidates. Set needs_clarification true when the visual "
            "evidence and language context do not separate the alternatives. Do not authorize "
            "speech.\n\n"
            f"Original visual transcription: {original_text}\n"
            f"Candidates (JSON): {json.dumps(candidates, ensure_ascii=False)}\n"
            f"Visual decoder evidence (raw scores, not probabilities): "
            f"{json.dumps(candidate_scores or [], ensure_ascii=False)}\n"
            f"Conversation context: {context or '(none)'}"
        )
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InterpretationResult,
                temperature=0.0,
                top_p=0.1,
                candidate_count=1,
                max_output_tokens=256,
                seed=7,
            ),
        )
        if getattr(response, "parsed", None) is not None:
            result = response.parsed
            if isinstance(result, InterpretationResult):
                return self._sanitize_and_gate(result, original_text, candidates)
        return self._sanitize_and_gate(
            InterpretationResult.model_validate_json(response.text), original_text, candidates
        )

    @classmethod
    def _sanitize_and_gate(
        cls, result: InterpretationResult, original_text: str, supplied_candidates: list[str]
    ) -> InterpretationResult:
        """Treat Gemini as an untrusted proposal and constrain its claims."""
        supplied = list(dict.fromkeys(item.strip() for item in supplied_candidates if item.strip()))
        normalized = {item.casefold(): item for item in supplied}
        selected = normalized.get(result.corrected_text.strip().casefold())
        if selected is None:
            selected = supplied[0]
        checks = []
        source_words = {word.casefold() for word in re.findall(r"[A-Za-z']+", original_text)}
        candidate_word_alternatives: set[str] = set()
        candidate_word_lists = [
            re.findall(r"[A-Za-z']+", candidate.casefold()) for candidate in supplied
        ]
        for index in range(max((len(words) for words in candidate_word_lists), default=0)):
            alternatives = {
                words[index]
                for words in candidate_word_lists
                if index < len(words)
            }
            if len(alternatives) > 1:
                candidate_word_alternatives.update(alternatives)
        for check in result.word_checks:
            observed = check.observed_word.strip()
            alternatives = [item.strip() for item in check.alternatives if item.strip()]
            plausible = any(
                frozenset({observed.casefold(), alternative.casefold()}) <= group
                for group in _VISUAL_CONFUSION_GROUPS
                for alternative in alternatives
            )
            candidate_grounded = (
                observed.casefold() in source_words
                and alternatives
                and all(item.casefold() in candidate_word_alternatives for item in alternatives)
            )
            if (plausible or candidate_grounded) and observed.casefold() in source_words:
                checks.append(check.model_copy(update={"alternatives": alternatives[:4]}))
        sanitized = InterpretationResult.model_validate(
            {
                **result.model_dump(),
                "original_text": original_text,
                "candidates": supplied,
                "selected_index": supplied.index(selected),
                "corrected_text": selected,
                "word_checks": checks,
            }
        )
        if selected != result.corrected_text:
            question = result.clarification_question
            if not question and len(supplied) > 1:
                question = f"Did you mean {supplied[0]} or {supplied[1]}?"
            if not question:
                question = "Please re-mouth the sentence or type what you intended."
            sanitized = sanitized.model_copy(
                update={
                    "needs_clarification": True,
                    "clarification_question": question,
                }
            )
        return cls._apply_word_safety_gate(sanitized)

    @staticmethod
    def _apply_word_safety_gate(result: InterpretationResult) -> InterpretationResult:
        """Never allow a low-confidence word to pass as a high-confidence sentence."""

        uncertain = [
            check for check in result.word_checks
            if check.confidence < WORD_CONFIDENCE_THRESHOLD or check.needs_clarification
        ]
        if not uncertain:
            return result
        question = result.clarification_question
        if not question:
            check = uncertain[0]
            question = f"Did you mean {check.observed_word} or {check.alternatives[0]}?"
        return InterpretationResult.model_validate(
            {
                **result.model_dump(),
                "needs_clarification": True,
                "clarification_question": question,
            }
        )

    async def propose_correction(self, candidates: list[str], context: str = "") -> str:
        """Compatibility helper returning only the selected text."""

        result = await self.interpret(candidates[0], candidates, context)
        return result.corrected_text

