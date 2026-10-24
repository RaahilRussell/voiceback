"""Turns ambiguity into short, accessible yes/no questions."""


class ClarificationEngine:
    def question_for(self, candidates: list[str]) -> str | None:
        return None if len(candidates) < 2 else f"Did you mean {candidates[0]}?"

