"""Gemini context and candidate correction boundary."""


class GeminiClient:
    async def propose_correction(self, candidates: list[str], context: str = "") -> str:
        raise NotImplementedError("Google GenAI integration is intentionally deferred")

