"""
throwaway_demo.py — temporary module for build-prompt demonstration.
"""


def add(a: int, b: int) -> int:
    """Return the sum of a and b.

    Parameters
    ----------
    a, b : int

    Returns
    -------
    int
        a + b

    Raises
    ------
    TypeError
        If either argument is not an int.

    Examples
    --------
    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    """
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Both arguments must be integers.")
    return a + b
