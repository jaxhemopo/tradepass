"""Correctness checking per question_type.

The engine stores the correct answer differently for each format:
  single_choice    -> list of one option id, e.g. ["a"]
  multiple_select  -> list of option ids, e.g. ["a","c"]
  exact_value      -> {answers: [str,...], unit: str, tolerance: float}

These helpers normalise the user's submission against the stored answer.
"""

from __future__ import annotations

from typing import Any


def _normalise_text(s: str) -> str:
    return s.strip().replace(",", ".").lower()


def _to_float(s: str) -> float | None:
    try:
        return float(_normalise_text(s))
    except (TypeError, ValueError):
        return None


def is_correct(question_type: str, picked: Any, correct: Any) -> bool:
    if question_type == "single_choice":
        if not isinstance(picked, str) or not isinstance(correct, list) or not correct:
            return False
        return picked == correct[0]

    if question_type == "multiple_select":
        if not isinstance(picked, list) or not isinstance(correct, list):
            return False
        return set(picked) == set(correct)

    if question_type == "exact_value":
        if not isinstance(picked, str) or not isinstance(correct, dict):
            return False
        answers = correct.get("answers") or []
        if not answers:
            return False
        tolerance = float(correct.get("tolerance") or 0.0)
        picked_norm = _normalise_text(picked)
        if any(_normalise_text(str(a)) == picked_norm for a in answers):
            return True
        picked_num = _to_float(picked)
        if picked_num is None:
            return False
        for a in answers:
            a_num = _to_float(str(a))
            if a_num is None:
                continue
            if tolerance == 0:
                if abs(picked_num - a_num) < 1e-9:
                    return True
            else:
                if abs(picked_num - a_num) <= abs(a_num * tolerance) + 1e-9:
                    return True
        return False

    return False
