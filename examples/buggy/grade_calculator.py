"""
grade_calculator.py
===================
Functions for converting numeric scores to letter grades and computing averages.
"""


def score_to_grade(score: int | float) -> str:
    """Convert a numeric score to a letter grade.

    Parameters
    ----------
    score : int or float
        The numeric score to convert.  Must be in the inclusive range [0, 100].

    Returns
    -------
    str
        The letter grade:
          "A"  for scores from 90 to 100 (inclusive on both ends)
          "B"  for scores from 80 to 89 (inclusive on both ends)
          "C"  for scores from 70 to 79 (inclusive on both ends)
          "D"  for scores from 60 to 69 (inclusive on both ends)
          "F"  for scores strictly less than 60 (i.e., 0 to 59 inclusive)

    Raises
    ------
    TypeError
        If ``score`` is not an int or float, or if it is a bool.
        (bool is a subclass of int in Python and is explicitly rejected.)
    ValueError
        If ``score`` is a valid number but is less than 0 or greater than 100.

    Examples
    --------
    >>> score_to_grade(95)
    'A'
    >>> score_to_grade(85)
    'B'
    >>> score_to_grade(75)
    'C'
    >>> score_to_grade(65)
    'D'
    >>> score_to_grade(55)
    'F'
    >>> score_to_grade(90)
    'A'
    >>> score_to_grade(80)
    'B'
    >>> score_to_grade(70)
    'C'
    >>> score_to_grade(60)
    'D'
    """
    if isinstance(score, bool):
        raise TypeError("score must be int or float, not bool")
    if not isinstance(score, (int, float)):
        raise TypeError(f"score must be int or float, got {type(score).__name__}")
    if score < 0 or score > 100:
        raise ValueError(f"score must be between 0 and 100 inclusive, got {score}")
    if score > 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def average(scores: list) -> float:
    """Return the arithmetic mean of a non-empty list of numbers.

    Parameters
    ----------
    scores : list
        A non-empty list of int or float values.

    Returns
    -------
    float
        The arithmetic mean: sum(scores) / len(scores).

    Raises
    ------
    ValueError
        If ``scores`` is an empty list.
    TypeError
        If ``scores`` is not a list.

    Examples
    --------
    >>> average([80, 90, 100])
    90.0
    >>> average([70])
    70.0
    >>> average([0, 100])
    50.0
    """
    if not isinstance(scores, list):
        raise TypeError(f"scores must be a list, got {type(scores).__name__}")
    if len(scores) == 0:
        raise ValueError("scores must not be empty")
    return sum(scores) / len(scores)
