"""Single-call Gemini correction, ranking, confidence, and clarification."""

from __future__ import annotations

import asyncio
import json
from functools import lru_cache

from app.schemas.interpretation import InterpretationResult


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
            self._interpret_sync, original_text.strip(), normalized_candidates, context.strip()
        )

    def _interpret_sync(
        self, original_text: str, candidates: list[str], context: str
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
            "You are the VoiceBack interpretation layer. Return exactly one JSON decision. "
            "Choose only among the supplied candidate sentences; never invent, rewrite, or "
            "combine words. Use context only to rank candidates. Set needs_clarification true "
            "when the evidence is ambiguous or confidence is below 0.80. Ask one short yes/no "
            "question when clarification is needed. Do not treat this response as approval to speak.\n\n"
            f"Original visual transcription: {original_text}\n"
            f"Candidates (JSON): {json.dumps(candidates, ensure_ascii=False)}\n"
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
                return result
        return InterpretationResult.model_validate_json(response.text)

    async def propose_correction(self, candidates: list[str], context: str = "") -> str:
        """Compatibility helper returning only the selected text."""

        result = await self.interpret(candidates[0], candidates, context)
        return result.corrected_text

