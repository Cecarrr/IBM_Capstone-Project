"""
test_grade_calculator_strong.py
================================
hand-written reference, not agent output.

Strong test suite for grade_calculator.py.
All expected values derived from the docstring specification only.
"""
import pytest
from grade_calculator import average, score_to_grade


# =============================================================================
# score_to_grade -- Happy Path
# =============================================================================

def test_score_to_grade__midpoint_a():
    # Docstring: 90-100 -> "A"; 95 is a representative interior point
    assert score_to_grade(95) == "A"


def test_score_to_grade__midpoint_b():
    # Docstring: 80-89 -> "B"
    assert score_to_grade(85) == "B"


def test_score_to_grade__midpoint_c():
    # Docstring: 70-79 -> "C"
    assert score_to_grade(75) == "C"


def test_score_to_grade__midpoint_d():
    # Docstring: 60-69 -> "D"
    assert score_to_grade(65) == "D"


def test_score_to_grade__midpoint_f():
    # Docstring: <60 -> "F"
    assert score_to_grade(55) == "F"


def test_score_to_grade__float_input():
    # Docstring accepts float; 89.9 is in the B range
    assert score_to_grade(89.9) == "B"


# =============================================================================
# score_to_grade -- Boundary Values
# =============================================================================

def test_score_to_grade__boundary_90_is_A():
    # Docstring: "A" for scores from 90 to 100 inclusive -- 90 must be "A"
    assert score_to_grade(90) == "A"


def test_score_to_grade__boundary_89_is_B():
    # Docstring: "B" for 80-89 inclusive -- 89 is the upper boundary of B
    assert score_to_grade(89) == "B"


def test_score_to_grade__boundary_80_is_B():
    # Docstring: "B" lower boundary
    assert score_to_grade(80) == "B"


def test_score_to_grade__boundary_79_is_C():
    assert score_to_grade(79) == "C"


def test_score_to_grade__boundary_70_is_C():
    assert score_to_grade(70) == "C"


def test_score_to_grade__boundary_69_is_D():
    assert score_to_grade(69) == "D"


def test_score_to_grade__boundary_60_is_D():
    assert score_to_grade(60) == "D"


def test_score_to_grade__boundary_59_is_F():
    assert score_to_grade(59) == "F"


def test_score_to_grade__boundary_0_is_F():
    # Docstring: lower bound 0 -> "F"
    assert score_to_grade(0) == "F"


def test_score_to_grade__boundary_100_is_A():
    # Docstring: upper bound 100 -> "A"
    assert score_to_grade(100) == "A"


# =============================================================================
# score_to_grade -- Invalid Input / Exceptions
# =============================================================================

def test_score_to_grade__raises_for_below_zero():
    with pytest.raises(ValueError):
        score_to_grade(-1)


def test_score_to_grade__raises_for_above_100():
    with pytest.raises(ValueError):
        score_to_grade(101)


def test_score_to_grade__raises_for_string():
    with pytest.raises(TypeError):
        score_to_grade("90")


def test_score_to_grade__raises_for_none():
    with pytest.raises(TypeError):
        score_to_grade(None)


def test_score_to_grade__raises_for_bool():
    # Docstring: bool is explicitly rejected even though bool is a subclass of int
    with pytest.raises(TypeError):
        score_to_grade(True)


# =============================================================================
# score_to_grade -- Equivalence Partitions
# =============================================================================

def test_score_to_grade__partition_a_range():
    # All values from 90 to 100 belong to the "A" partition
    for s in (90, 91, 99, 100):
        assert score_to_grade(s) == "A", f"Expected A for score {s}"


def test_score_to_grade__partition_f_range():
    # All values from 0 to 59 belong to the "F" partition
    for s in (0, 1, 30, 59):
        assert score_to_grade(s) == "F", f"Expected F for score {s}"


# =============================================================================
# average -- Happy Path
# =============================================================================

def test_average__three_values():
    # Docstring example: average([80, 90, 100]) == 90.0
    assert average([80, 90, 100]) == 90.0


def test_average__single_value():
    # Docstring example: average([70]) == 70.0
    assert average([70]) == 70.0


def test_average__symmetric():
    # Docstring example: average([0, 100]) == 50.0
    assert average([0, 100]) == 50.0


# =============================================================================
# average -- Boundary Values
# =============================================================================

def test_average__single_element_list():
    # Boundary: minimum non-empty list
    assert average([42]) == 42.0


def test_average__two_elements():
    assert average([10, 20]) == 15.0


# =============================================================================
# average -- Invalid Input / Exceptions
# =============================================================================

def test_average__raises_for_empty_list():
    with pytest.raises(ValueError):
        average([])


def test_average__raises_for_non_list():
    with pytest.raises(TypeError):
        average((80, 90))


# =============================================================================
# average -- Equivalence Partitions
# =============================================================================

def test_average__all_same_values():
    # Partition: when all elements are equal, mean equals that value
    assert average([5, 5, 5]) == 5.0


def test_average__negative_values():
    # Partition: list containing negative numbers
    assert average([-10, -20]) == -15.0


# =============================================================================
# COVERAGE SUMMARY
# =============================================================================
# Function: score_to_grade
#   Happy path       : 6 test(s) -- midpoints for all 5 grades, float input
#   Boundary values  : 10 test(s) -- all grade boundaries (90,89,80,79,70,69,60,59,0,100)
#   Invalid input    : 5 test(s) -- below 0, above 100, str, None, bool
#   Equiv. partitions: 2 test(s) -- A range, F range
#
# Function: average
#   Happy path       : 3 test(s) -- docstring examples
#   Boundary values  : 2 test(s) -- single element, two elements
#   Invalid input    : 2 test(s) -- empty list, non-list
#   Equiv. partitions: 2 test(s) -- all-same, negative values
#
# =============================================================================
# ASSUMPTIONS
# =============================================================================
# [A1] score_to_grade: float values like 89.9 follow the same boundaries as integers.
#      The docstring does not give a float example for boundary values, but states
#      the parameter is "int or float", so this is treated as specified behaviour.
# [A2] average: the function accepts a list containing floats and integers mixed;
#      the docstring says "list of int or float values" and does not restrict mixing.
# =============================================================================
