"""Cartesia speech synthesis boundary."""


class CartesiaClient:
    async def synthesize(self, text: str, voice_id: str) -> bytes:
        raise NotImplementedError("Cartesia integration is intentionally deferred")

