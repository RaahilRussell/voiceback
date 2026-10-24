import pytest
from pydantic import ValidationError

from app.schemas.interpretation import InterpretationResult


def test_interpretation_requires_selected_candidate() -> None:
    result = InterpretationResult(
        original_text="this is the ground truth",
        corrected_text="this is the ground truth",
        candidates=["this is the ground truth", "they turned around"],
        selected_index=0,
        confidence=0.82,
        needs_clarification=False,
    )
    assert result.corrected_text == result.candidates[result.selected_index]


def test_interpretation_requires_question_when_uncertain() -> None:
    with pytest.raises(ValidationError):
        InterpretationResult(
            original_text="this is the ground truth",
            corrected_text="this is the ground truth",
            candidates=["this is the ground truth"],
            selected_index=0,
            confidence=0.42,
            needs_clarification=True,
        )
