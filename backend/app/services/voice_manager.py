"""Consent and enrollment state boundary for personal voices."""

class VoiceManager:
    def __init__(self) -> None:
        self._voices: dict[str, str] = {}
        self._consented: set[str] = set()

    def require_consent(self, user_id: str) -> None:
        if user_id not in self._consented:
            raise PermissionError("explicit voice enrollment consent is required")

    def enroll(self, user_id: str, consent: bool, voice_id: str | None) -> None:
        if not consent:
            raise PermissionError("voice enrollment requires explicit consent")
        self._consented.add(user_id)
        if voice_id:
            self._voices[user_id] = voice_id

    def voice_id(self, user_id: str, override: str | None = None) -> str:
        self.require_consent(user_id)
        selected = override or self._voices.get(user_id)
        if not selected:
            raise ValueError("no enrolled voice is configured")
        return selected

