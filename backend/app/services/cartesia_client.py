"""Cartesia speech synthesis boundary using the provider's HTTPS API."""

import base64

import httpx

from app.config import settings


class CartesiaClient:
    async def synthesize(self, text: str, voice_id: str) -> bytes:
        if not settings.cartesia_api_key:
            raise RuntimeError("CARTESIA_API_KEY is required for speech synthesis")
        if not text.strip() or not voice_id.strip():
            raise ValueError("approved text and voice_id are required")
        payload = {
            "model_id": settings.cartesia_model,
            "transcript": text.strip(),
            "voice": {"mode": "id", "id": voice_id},
            "output_format": {"container": "mp3", "encoding": "mp3", "sample_rate": 44100},
        }
        headers = {
            "X-API-Key": settings.cartesia_api_key,
            "Cartesia-Version": settings.cartesia_version,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.cartesia.ai/tts/bytes", json=payload, headers=headers)
        response.raise_for_status()
        return response.content

    async def synthesize_base64(self, text: str, voice_id: str) -> str:
        return base64.b64encode(await self.synthesize(text, voice_id)).decode("ascii")

