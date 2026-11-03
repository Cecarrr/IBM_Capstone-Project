"""
Tests for throwaway_demo.add — WEAK suite (happy path only).
Derived from the docstring only.
"""
from throwaway_demo import add


def test_add__basic():
    # Only one happy-path case — intentionally weak to show low mutation score.
    assert add(2, 3) == 5
