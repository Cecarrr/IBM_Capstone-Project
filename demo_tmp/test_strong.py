"""
Tests for throwaway_demo.add — STRONG suite.
Derived from the docstring only.
"""
import pytest
from throwaway_demo import add


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_add__positive_integers():
    # Docstring: add(2, 3) -> 5
    assert add(2, 3) == 5


def test_add__negative_integers():
    # Docstring: add(-1, 1) -> 0
    assert add(-1, 1) == 0


# ---------------------------------------------------------------------------
# Boundary values
# ---------------------------------------------------------------------------

def test_add__both_zero():
    # Boundary: 0 + 0 = 0
    assert add(0, 0) == 0


def test_add__large_positive():
    # Boundary: large values should still return a + b
    assert add(10**6, 10**6) == 2_000_000


def test_add__large_negative():
    assert add(-10**6, -10**6) == -2_000_000


# ---------------------------------------------------------------------------
# Invalid input / exceptions
# ---------------------------------------------------------------------------

def test_add__raises_for_float_a():
    # Docstring: raises TypeError if either argument is not an int.
    with pytest.raises(TypeError):
        add(1.5, 2)


def test_add__raises_for_float_b():
    with pytest.raises(TypeError):
        add(2, 1.5)


def test_add__raises_for_string():
    with pytest.raises(TypeError):
        add("hello", 1)


def test_add__raises_for_none():
    with pytest.raises(TypeError):
        add(None, 1)


# ---------------------------------------------------------------------------
# Equivalence partitions
# ---------------------------------------------------------------------------

def test_add__both_negative():
    # Partition: both operands negative -> result is more negative
    assert add(-3, -4) == -7


def test_add__one_zero():
    # Partition: identity — adding zero to any int returns the int
    assert add(5, 0) == 5
    assert add(0, 5) == 5
