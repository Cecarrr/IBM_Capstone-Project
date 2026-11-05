"""Tests for grade_calculator.py — generated from the docstring specification."""
import pytest

from grade_calculator import average, score_to_grade


# =============================================================================
# score_to_grade
# =============================================================================

# --- Happy Path ---------------------------------------------------------------

def test_score_to_grade__midpoint_a():
    # Docstring: "A" for scores from 90 to 100 (inclusive); 95 is a clear interior point.
    assert score_to_grade(95) == "A"


def test_score_to_grade__midpoint_b():
    # Docstring: "B" for scores from 80 to 89 (inclusive); 85 is a clear interior point.
    assert score_to_grade(85) == "B"


def test_score_to_grade__midpoint_c():
    # Docstring: "C" for scores from 70 to 79 (inclusive); 75 is a clear interior point.
    assert score_to_grade(75) == "C"


def test_score_to_grade__midpoint_d():
    # Docstring: "D" for scores from 60 to 69 (inclusive); 65 is a clear interior point.
    assert score_to_grade(65) == "D"


def test_score_to_grade__midpoint_f():
    # Docstring: "F" for scores strictly less than 60; 55 is a clear interior point.
    assert score_to_grade(55) == "F"


def test_score_to_grade__float_input_b_range():
    # Docstring accepts int or float; 84.5 is in the B range.
    assert score_to_grade(84.5) == "B"


# --- Boundary Values ----------------------------------------------------------

def test_score_to_grade__boundary_100_is_a():
    # Docstring: "A" is inclusive of 100 (upper bound of entire range).
    assert score_to_grade(100) == "A"


def test_score_to_grade__boundary_90_is_a():
    # Docstring: "A" lower boundary — 90 must be "A", not "B".
    assert score_to_grade(90) == "A"


def test_score_to_grade__boundary_89_is_b():
    # Docstring: "B" upper boundary — 89 is the highest score that returns "B".
    assert score_to_grade(89) == "B"


def test_score_to_grade__boundary_80_is_b():
    # Docstring: "B" lower boundary — 80 must be "B", not "C".
    assert score_to_grade(80) == "B"


def test_score_to_grade__boundary_79_is_c():
    # Docstring: "C" upper boundary — 79 is the highest score returning "C".
    assert score_to_grade(79) == "C"


def test_score_to_grade__boundary_70_is_c():
    # Docstring: "C" lower boundary — 70 must be "C", not "D".
    assert score_to_grade(70) == "C"


def test_score_to_grade__boundary_69_is_d():
    # Docstring: "D" upper boundary — 69 is the highest score returning "D".
    assert score_to_grade(69) == "D"


def test_score_to_grade__boundary_60_is_d():
    # Docstring: "D" lower boundary — 60 must be "D", not "F".
    assert score_to_grade(60) == "D"


def test_score_to_grade__boundary_59_is_f():
    # Docstring: "F" for strictly less than 60 — 59 is the highest score returning "F".
    assert score_to_grade(59) == "F"


def test_score_to_grade__boundary_0_is_f():
    # Docstring: valid range is [0, 100]; 0 is the lower bound and must return "F".
    assert score_to_grade(0) == "F"


# --- Invalid Input / Exceptions -----------------------------------------------

def test_score_to_grade__raises_value_error_for_negative():
    # Docstring: ValueError if score < 0.
    with pytest.raises(ValueError):
        score_to_grade(-1)


def test_score_to_grade__raises_value_error_for_above_100():
    # Docstring: ValueError if score > 100.
    with pytest.raises(ValueError):
        score_to_grade(101)


def test_score_to_grade__raises_type_error_for_string():
    # Docstring: TypeError if score is not int or float.
    with pytest.raises(TypeError):
        score_to_grade("90")


def test_score_to_grade__raises_type_error_for_none():
    # Docstring: TypeError if score is not int or float.
    with pytest.raises(TypeError):
        score_to_grade(None)


def test_score_to_grade__raises_type_error_for_bool_true():
    # Docstring: bool is explicitly rejected even though bool is a subclass of int.
    with pytest.raises(TypeError):
        score_to_grade(True)


def test_score_to_grade__raises_type_error_for_bool_false():
    # Docstring: bool is explicitly rejected.
    with pytest.raises(TypeError):
        score_to_grade(False)


# --- Equivalence Partitions ---------------------------------------------------

def test_score_to_grade__partition_a_range_interior():
    # Partition: all scores in 91–99 behave identically to 90 and 100 (returns "A").
    assert score_to_grade(92) == "A"


def test_score_to_grade__partition_b_range_interior():
    # Partition: all scores in 81–88 behave identically to 80 and 89 (returns "B").
    assert score_to_grade(83) == "B"


def test_score_to_grade__partition_c_range_interior():
    # Partition: all scores in 71–78 behave identically to 70 and 79 (returns "C").
    assert score_to_grade(73) == "C"


def test_score_to_grade__partition_d_range_interior():
    # Partition: all scores in 61–68 behave identically to 60 and 69 (returns "D").
    assert score_to_grade(63) == "D"


def test_score_to_grade__partition_f_range_interior():
    # Partition: all scores in 1–58 behave identically to 0 and 59 (returns "F").
    assert score_to_grade(30) == "F"


def test_score_to_grade__partition_above_range():
    # Partition: all scores > 100 raise ValueError (101 and 200 are the same class).
    with pytest.raises(ValueError):
        score_to_grade(200)


def test_score_to_grade__partition_below_range():
    # Partition: all scores < 0 raise ValueError (-100 is same class as -1).
    with pytest.raises(ValueError):
        score_to_grade(-100)


# =============================================================================
# average
# =============================================================================

# --- Happy Path ---------------------------------------------------------------

def test_average__three_values_from_docstring():
    # Docstring example: average([80, 90, 100]) == 90.0
    assert average([80, 90, 100]) == 90.0


def test_average__single_value_from_docstring():
    # Docstring example: average([70]) == 70.0
    assert average([70]) == 70.0


def test_average__symmetric_pair_from_docstring():
    # Docstring example: average([0, 100]) == 50.0
    assert average([0, 100]) == 50.0


def test_average__returns_float():
    # Docstring: return type is float; average of two equal ints is still a float.
    result = average([5, 5])
    assert isinstance(result, float)
    assert result == 5.0


# --- Boundary Values ----------------------------------------------------------

def test_average__single_element_list():
    # Boundary: minimum non-empty list (length 1); result equals that element.
    assert average([42]) == 42.0


def test_average__two_elements():
    # Boundary: two-element list; result is their arithmetic mean.
    assert average([10, 20]) == 15.0


def test_average__all_zeros():
    # Boundary: all elements are 0; mean is 0.0.
    assert average([0, 0, 0]) == 0.0


# --- Invalid Input / Exceptions -----------------------------------------------

def test_average__raises_value_error_for_empty_list():
    # Docstring: ValueError if scores is an empty list.
    with pytest.raises(ValueError):
        average([])


def test_average__raises_type_error_for_tuple():
    # Docstring: TypeError if scores is not a list.
    with pytest.raises(TypeError):
        average((80, 90, 100))


def test_average__raises_type_error_for_string():
    # Docstring: TypeError if scores is not a list.
    with pytest.raises(TypeError):
        average("80,90,100")


def test_average__raises_type_error_for_none():
    # Docstring: TypeError if scores is not a list.
    with pytest.raises(TypeError):
        average(None)


# --- Equivalence Partitions ---------------------------------------------------

def test_average__all_same_values():
    # Partition: when all elements are equal, mean equals that value.
    assert average([7, 7, 7, 7]) == 7.0


def test_average__negative_values():
    # Partition: list containing negative numbers; mean is negative.
    assert average([-10, -20, -30]) == -20.0


def test_average__mixed_int_and_float():
    # Partition: list with both int and float elements.
    # Docstring says "int or float values"; mixing is implied as valid.
    # ASSUMPTION [A1]: mixing int and float in one list is allowed.
    assert average([1, 2.0, 3]) == 2.0


def test_average__large_list():
    # Partition: list with many elements; mean of 1..10 is 5.5.
    assert average([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 5.5


# =============================================================================
# COVERAGE SUMMARY
# =============================================================================
# Function: score_to_grade
#   Happy path       : 6 test(s) -- five grade midpoints plus a float input
#   Boundary values  : 11 test(s) -- every grade boundary (0, 59/60, 69/70, 79/80, 89/90, 100)
#   Invalid input    : 6 test(s) -- negative, above 100, str, None, bool True, bool False
#   Equiv. partitions: 7 test(s) -- interior of each grade band, above/below range
#
# Function: average
#   Happy path       : 4 test(s) -- three docstring examples plus float return type
#   Boundary values  : 3 test(s) -- single element, two elements, all zeros
#   Invalid input    : 4 test(s) -- empty list, tuple, string, None
#   Equiv. partitions: 4 test(s) -- all-same, negative, mixed int/float, large list
#
# =============================================================================
# ASSUMPTIONS
# =============================================================================
# [A1] average: mixing int and float values in a single list is valid input.
#      The docstring says "int or float values" without forbidding mixing; a
#      mixed list should be accepted and produce the correct arithmetic mean.
# =============================================================================
