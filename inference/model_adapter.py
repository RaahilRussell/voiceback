class ModelAdapter:
    """Small stable interface around the eventual Auto-AVSR implementation."""

    def __init__(self, checkpoint_path: str | None = None, device: str = "auto") -> None:
        self.checkpoint_path = checkpoint_path
        self.device = device

    def transcribe_video(self, video_path: str) -> list[str]:
        raise NotImplementedError("Configure Auto-AVSR before running inference")

