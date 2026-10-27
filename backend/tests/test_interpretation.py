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


def test_unlisted_gemini_rewrite_is_not_authorized() -> None:
    result = InterpretationResult(
        original_text="YAHOO IS THIS",
        corrected_text="YO WHO IS THIS",
        candidates=["YAHOO IS THIS", "YO WHO IS THIS"],
        selected_index=1,
        confidence=0.90,
        needs_clarification=False,
    )
    gated = GeminiClient._sanitize_and_gate(
        result, "YAHOO IS THIS", ["YAHOO IS THIS"]
    )
    assert gated.corrected_text == "YAHOO IS THIS"
    assert gated.needs_clarification is True
    assert gated.clarification_question == "Please re-mouth the sentence or type what you intended."


def test_context_review_routes_known_lip_confusion_even_with_large_margin() -> None:
    assert GeminiClient.should_review(
        "I AM A PRO",
        ["I AM A PRO", "I AM A BRO"],
        [{"raw_score": -1.0}, {"raw_score": -4.0}],
    ) is True


def test_context_review_skips_easy_high_margin_candidates() -> None:
    assert GeminiClient.should_review(
        "THIS IS THE GROUND TRUTH",
        ["THIS IS THE GROUND TRUTH", "THIS IS THE GROUND TRUCE"],
        [{"raw_score": -1.0}, {"raw_score": -3.5}],
    ) is False


def test_context_review_routes_low_margin_candidate_disagreement() -> None:
    assert GeminiClient.should_review(
        "THIS IS THE GROUND TRUTH",
        ["THIS IS THE GROUND TRUTH", "THIS IS THE GROUND TRUCE"],
        [{"raw_score": -1.0}, {"raw_score": -1.4}],
    ) is True
