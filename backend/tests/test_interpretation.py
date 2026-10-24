import pytest
from pydantic import ValidationError

from app.schemas.interpretation import InterpretationResult, WordCheck
from app.services.gemini_client import GeminiClient


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


def test_low_confidence_word_forces_clarification_even_with_high_sentence_score() -> None:
    with pytest.raises(ValidationError):
        InterpretationResult(
            original_text="I AM A PRO",
            corrected_text="I AM A PRO",
            candidates=["I AM A PRO"],
            selected_index=0,
            confidence=0.96,
            needs_clarification=False,
            word_checks=[
                WordCheck(
                    observed_word="PRO",
                    alternatives=["BRO"],
                    confidence=0.51,
                    needs_clarification=True,
                )
            ],
        )


def test_word_safety_gate_locks_uncertain_word() -> None:
    result = InterpretationResult(
        original_text="I AM A PRO",
        corrected_text="I AM A PRO",
        candidates=["I AM A PRO"],
        selected_index=0,
        confidence=0.96,
        needs_clarification=True,
        clarification_question="Did you mean PRO or BRO?",
        word_checks=[
            WordCheck(
                observed_word="PRO",
                alternatives=["BRO"],
                confidence=0.51,
                needs_clarification=True,
            )
        ],
    )
    gated = GeminiClient._apply_word_safety_gate(result)
    assert gated.needs_clarification is True
    assert gated.clarification_question == "Did you mean PRO or BRO?"
