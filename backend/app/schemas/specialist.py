"""Contracts for optional, trained visual ambiguity specialists."""

from typing import Literal

from pydantic import BaseModel, Field


class SpecialistEvidence(BaseModel):
    """Evidence returned by a specialist, never an uncalibrated prediction."""

    specialist: str
    status: Literal["available", "unavailable", "abstained"]
    supported_groups: list[str] = Field(default_factory=list)
    note: str | None = None
    candidate_scores: dict[str, float] = Field(default_factory=dict)


class VisualAmbiguitySpecialist:
    """Explicit extension point for a trained viseme specialist.

    The initial implementation deliberately abstains. It prevents the product
    from treating a heuristic as a trained P/B/M or F/V expert.
    """

    name = "unavailable"
    supported_groups = ("P/B/M", "F/V", "other-viseme-confusions")

    def analyze(self, _video_region: object, _candidates: list[str]) -> SpecialistEvidence:
        return SpecialistEvidence(
            specialist=self.name,
            status="unavailable",
            supported_groups=list(self.supported_groups),
            note="No trained specialist weights are configured.",
        )
