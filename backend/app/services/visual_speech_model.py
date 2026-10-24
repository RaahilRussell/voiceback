"""Auto-AVSR visual-only inference boundary; never accepts microphone audio."""


class VisualSpeechModel:
    def predict(self, video_path: str) -> list[str]:
        raise NotImplementedError("Load the configured visual-only model adapter")

