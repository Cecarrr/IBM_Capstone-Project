"""
date_overlap.py
===============
Function for checking whether two date ranges overlap.
"""
import datetime


def ranges_overlap(
    start1: datetime.date,
    end1: datetime.date,
    start2: datetime.date,
    end2: datetime.date,
) -> bool:
    """Return True if two inclusive date ranges overlap, False otherwise.

    Both ranges are INCLUSIVE of their start and end dates.  Two ranges
    overlap if they share at least one calendar day in common, including
    the case where one range ends on the exact same day that the other begins
    (i.e., ranges that touch on exactly one day DO overlap).

    Overlap condition (derived from the inclusive definition):
        start1 <= end2  AND  start2 <= end1

    Parameters
    ----------
    start1 : datetime.date
        The first day of the first range (inclusive).
    end1 : datetime.date
        The last day of the first range (inclusive).  Must be >= start1.
    start2 : datetime.date
        The first day of the second range (inclusive).
    end2 : datetime.date
        The last day of the second range (inclusive).  Must be >= start2.

    Returns
    -------
    bool
        True if the two ranges share at least one calendar day.
        False if the ranges are completely disjoint (no shared day).

    Raises
    ------
    TypeError
        If any argument is not a ``datetime.date`` instance.
        Note: ``datetime.datetime`` is a subclass of ``datetime.date`` and is
        accepted without error.
    ValueError
        If ``end1`` is strictly before ``start1``, or if ``end2`` is strictly
        before ``start2``.

    Examples
    --------
    >>> from datetime import date
    >>> ranges_overlap(date(2024, 1, 1), date(2024, 1, 10),
    ...                date(2024, 1, 5), date(2024, 1, 15))
    True
    >>> ranges_overlap(date(2024, 1, 1), date(2024, 1, 5),
    ...                date(2024, 1, 5), date(2024, 1, 10))
    True
    >>> ranges_overlap(date(2024, 1, 1), date(2024, 1, 4),
    ...                date(2024, 1, 5), date(2024, 1, 10))
    False
    >>> ranges_overlap(date(2024, 1, 5), date(2024, 1, 10),
    ...                date(2024, 1, 1), date(2024, 1, 5))
    True
    """
    for arg in (start1, end1, start2, end2):
        if not isinstance(arg, datetime.date):
            raise TypeError(
                f"all arguments must be datetime.date instances, got {type(arg).__name__}"
            )
    if end1 < start1:
        raise ValueError(
            f"end1 ({end1}) must not be before start1 ({start1})"
        )
    if end2 < start2:
        raise ValueError(
            f"end2 ({end2}) must not be before start2 ({start2})"
        )
    return start1 <= end2 and start2 <= end1
