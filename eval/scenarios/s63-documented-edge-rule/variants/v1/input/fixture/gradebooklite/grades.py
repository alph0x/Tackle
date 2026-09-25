"""GradebookLite: percentages, rounding and letter grades.

Percentages are always rounded to the nearest whole number with round-half-up (a tie rounds away
from zero: 88.5 -> 89), matching the registrar's grading policy. Python's built-in round() uses
round-half-to-even ("banker's rounding") and must not be used on scores, because it would silently
misgrade a student whose exact average lands on .5 -- see round_half_up() below, which every report
in this module is built from.
"""
import math


def round_half_up(value: float) -> int:
    """Round `value` to the nearest integer, ties rounding away from zero.

    Scores in this module are never negative, so this only needs to handle zero and positive values.
    """
    return math.floor(value + 0.5)


def percentage(points: float, total: float) -> float:
    """Raw percentage (0-100), not rounded."""
    if total == 0:
        return 0.0
    return points / total * 100


LETTER_CUTOFFS = (("A", 90), ("B", 80), ("C", 70), ("D", 60))


def letter_grade(rounded_score: int) -> str:
    """Letter grade for an already-rounded whole-number percentage (inclusive cutoffs)."""
    for letter, cutoff in LETTER_CUTOFFS:
        if rounded_score >= cutoff:
            return letter
    return "F"


def report_card(name: str, score: float) -> str:
    """One-line report for a single student: 'Name: NN% (grade Letter)'.

    `score` is a raw percentage (0-100), rounded here with round_half_up().
    """
    rounded = round_half_up(score)
    return f"{name}: {rounded}% (grade {letter_grade(rounded)})"
