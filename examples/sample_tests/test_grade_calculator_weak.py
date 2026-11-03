"""
test_grade_calculator_weak.py
==============================
hand-written reference, not agent output.

Weak test suite for grade_calculator.py -- happy-path midpoints only.
Intentionally omits boundary values, exception tests, and equivalence partitions
so that `tcgen check` scores clearly lower than the strong suite.
"""
from grade_calculator import average, score_to_grade


# =============================================================================
# score_to_grade -- Happy Path only
# =============================================================================

def test_score_to_grade__midpoint_a():
    assert score_to_grade(95) == "A"


def test_score_to_grade__midpoint_b():
    assert score_to_grade(85) == "B"


def test_score_to_grade__midpoint_c():
    assert score_to_grade(75) == "C"


def test_score_to_grade__midpoint_d():
    assert score_to_grade(65) == "D"


def test_score_to_grade__midpoint_f():
    assert score_to_grade(55) == "F"


# =============================================================================
# average -- Happy Path only
# =============================================================================

def test_average__basic():
    assert average([80, 90, 100]) == 90.0


# =============================================================================
# COVERAGE SUMMARY
# =============================================================================
# Function: score_to_grade
#   Happy path       : 5 test(s) -- one midpoint per grade
#   Boundary values  : 0 test(s)
#   Invalid input    : 0 test(s)
#   Equiv. partitions: 0 test(s)
#
# Function: average
#   Happy path       : 1 test(s) -- docstring example
#   Boundary values  : 0 test(s)
#   Invalid input    : 0 test(s)
#   Equiv. partitions: 0 test(s)
# =============================================================================
