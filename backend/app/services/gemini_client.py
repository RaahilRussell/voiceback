"""Single-call Gemini correction, ranking, confidence, and clarification."""

from __future__ import annotations

import asyncio

from app.schemas.interpretation import InterpretationResult


class GeminiClient:
    def __init__(self, api_key: str | None, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.model = model

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

        return await asyncio.to_thread(self._interpret_sync, original_text, candidates, context)

    def _interpret_sync(
        self, original_text: str, candidates: list[str], context: str
    ) -> InterpretationResult:
        from google import genai

        client = genai.Client(api_key=self.api_key)
        prompt = (
            "You are the VoiceBack interpretation layer. Choose only among the supplied "
            "candidate sentences. Use context to rank them, but never invent a candidate. "
            "Set needs_clarification true when the evidence is ambiguous or confidence is "
            "below 0.80. Ask one short yes/no question when clarification is needed. "
            "Do not treat this response as user approval to speak.\n\n"
            f"Original visual transcription: {original_text}\n"
            f"Candidates: {candidates}\n"
            f"Conversation context: {context or '(none)'}"
        )
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": InterpretationResult,
            },
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

