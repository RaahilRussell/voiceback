"""Turns ambiguity into short, accessible yes/no questions."""


class ClarificationEngine:
    def question_for(self, candidates: list[str]) -> str | None:
        if len(candidates) < 2:
            return None
        return f"Did you mean {candidates[0]} or {candidates[1]}?"

    def resolve(self, candidates: list[str], answer: str) -> tuple[str | None, bool]:
        """Resolve an accessible yes/no or candidate-number answer safely."""
        normalized = answer.strip().lower()
        if normalized in {"yes", "y", "1", "first", "one"}:
            return candidates[0], False
        if normalized in {"no", "n", "2", "second", "two"} and len(candidates) == 2:
            return candidates[1], False
        if normalized.isdigit() and 1 <= int(normalized) <= len(candidates):
            return candidates[int(normalized) - 1], False
        return None, True

