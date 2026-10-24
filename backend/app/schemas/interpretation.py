"""Typed Gemini interpretation output used by the approval gate."""

from pydantic import BaseModel, Field, model_validator

WORD_CONFIDENCE_THRESHOLD = 0.80


class WordCheck(BaseModel):
    """A potentially ambiguous word that must be reviewed before speech."""

    observed_word: str = Field(min_length=1)
    alternatives: list[str] = Field(default_factory=list, max_length=4)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_clarification: bool

    @model_validator(mode="after")
    def validate_check(self) -> "WordCheck":
        if self.needs_clarification and not self.alternatives:
            raise ValueError("a low-confidence word must include an alternative")
        return self


class InterpretationResult(BaseModel):
    """One structured correction/ranking/clarification decision."""

    original_text: str = Field(description="The unmodified Auto-AVSR transcription.")
    corrected_text: str = Field(description="The best proposed interpretation.")
    candidates: list[str] = Field(min_length=1, max_length=5)
    selected_index: int = Field(ge=0, le=4)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_clarification: bool
    clarification_question: str | None = None
    word_checks: list[WordCheck] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_selection(self) -> "InterpretationResult":
        if self.selected_index >= len(self.candidates):
            raise ValueError("selected_index must refer to a candidate")
        if self.corrected_text != self.candidates[self.selected_index]:
            raise ValueError("corrected_text must equal the selected candidate")
        if self.needs_clarification and not self.clarification_question:
            raise ValueError("clarification_question is required when clarification is needed")
        if not self.needs_clarification and self.clarification_question is not None:
            raise ValueError("clarification_question must be null when clarification is not needed")
        if any(check.needs_clarification for check in self.word_checks) and not self.needs_clarification:
            raise ValueError("low-confidence word checks require clarification")
        return self
