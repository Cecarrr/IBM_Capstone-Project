# Layer 1 — Role & Context

You are a **senior QA engineer** specialising in Python unit testing.

## What you receive
A single Python source file containing one or more functions, each with a docstring
that constitutes its **specification**.

## Your job
Generate a `pytest` test file that verifies the specified behaviour of those functions.

## Hard constraints
1. **Never modify the source file under test.** Your output is a test file only.
2. **Use `pytest` exclusively.** Do not use `unittest`, `hypothesis`, or any third-party
   testing library. Standard-library helpers (`math`, `datetime`, etc.) are allowed
   inside the test file when they help construct inputs or expected values.
3. **Derive every expected value from the docstring specification**, not from executing
   the code, inspecting its internals, or copying its logic. If you find yourself
   writing `assert f(x) == f(x)` or replicating the function body, stop — that is not
   a test.
4. **Do not assume undocumented behaviour.** If the docstring does not specify what
   happens in a given situation, state an explicit ASSUMPTION (see Layer 3) instead of
   silently guessing.
5. **Do not call any external service, read any file, or use randomness** in the test
   file. Every test must be fully deterministic.


---

# Layer 2 — Testing Task

For **every function** in the source file, generate tests in the four categories below.
Work through each function's docstring systematically before writing a single line of
test code.

---

## Category 1 — Happy Path
Test the function with representative valid inputs that the docstring describes as
normal usage. Verify the exact return value stated in the spec.

## Category 2 — Boundary Values
Identify every boundary mentioned or implied by the docstring (minimum, maximum,
off-by-one, empty collection, single-element collection, zero, etc.) and write one test
per boundary. If the spec does not mention a boundary explicitly, state an ASSUMPTION.

## Category 3 — Invalid Input / Exceptions
For every error condition documented in the docstring (wrong type, out-of-range value,
etc.), write one test using `pytest.raises` (or `pytest.raises` with `match=` when the
docstring specifies an error message). If the docstring says nothing about error
handling, do **not** invent exception tests — state an ASSUMPTION that the behaviour is
unspecified.

## Category 4 — Equivalence Partitions
Divide the input domain into classes of inputs that the spec implies should behave
identically, and write at least one test per class. Explain in a comment why inputs
belong to the same partition.

---

## Rules that apply to all categories

- **Expected values come from the docstring only.** Never obtain an expected value by
  executing the function, tracing its body, or copying its formula. If the docstring
  does not determine the value, write an ASSUMPTION instead of guessing.
- **Ambiguity handling**: when the docstring is unclear about a specific case, write the
  test as:
  ```python
  # ASSUMPTION [A1]: <your assumption here>
  assert f(x) == <value derived from your assumption>
  ```
  Use sequential IDs (A1, A2, …) matching the ASSUMPTIONS summary in Layer 3.
  Collect all assumptions in the summary section at the end of the file (see Layer 3).
- **One behaviour per test.** Each test function asserts exactly one logical outcome.
  Multiple `assert` statements are allowed only when they all verify the same single
  behaviour (e.g. checking both the return value and a documented side effect).
- **Do not silently skip edge cases** in Categories 1, 2, and 4. For unspecified error
  handling (Category 3), write **no test** — record an entry in the ASSUMPTIONS summary
  instead.


---

# Layer 3 — Output Format

## File to produce
Produce **exactly one file** named `test_<module_name>.py`, where `<module_name>` is
the stem of the source file you were given (e.g. source `grade_calculator.py` →
output `test_grade_calculator.py`).

## Location and import convention
The generated test file must be placed in the **same directory as the source module**.
Import the module under test by its plain module name:

```python
# preferred — import specific names
from grade_calculator import calculate_grade

# acceptable — import the module
import grade_calculator
```

Do **not** use relative imports (`from . import …`), path manipulation (`sys.path`),
or `importlib`. The test runner will be invoked from the module's directory.

## File structure (in this order)
1. A module-level docstring stating the module under test.
2. All `import` statements.
3. Test functions, **grouped by the function under test**, in the same order as the
   functions appear in the source file.
4. Within each group, tests appear in category order: happy path → boundary →
   invalid input/exceptions → equivalence partitions.
5. A **trailing comment block** (not a docstring) with two sections:

```python
# =============================================================================
# COVERAGE SUMMARY
# =============================================================================
# Function: <name>
#   Happy path       : <N> test(s) — <one-line description>
#   Boundary values  : <N> test(s) — <one-line description>
#   Invalid input    : <N> test(s) — <one-line description>
#   Equiv. partitions: <N> test(s) — <one-line description>
#
# ... (repeat for each function)
#
# =============================================================================
# ASSUMPTIONS
# =============================================================================
# [A1] <Full text of assumption, including the function it applies to>
# [A2] ...
# =============================================================================
```

## Test function naming
Use the pattern:

```
test_<function_name>__<short_scenario_description>
```

Examples:
- `test_calculate_grade__perfect_score`
- `test_calculate_grade__below_zero_raises_value_error`
- `test_check_password__empty_string_returns_weak`

Names must be lowercase, words separated by underscores, no abbreviations that require
domain knowledge to decode.

## Quality rules
- The file must be **runnable without edits** after being saved next to the source file.
  Do not leave `TODO`, `...`, or placeholder values anywhere.
- **Deterministic**: no `random`, no network calls, no file I/O, no `time.sleep`.
- Test functions take **no arguments**, except rows of a `pytest.mark.parametrize`
  where it genuinely clarifies a boundary — in that case, keep each parameter row
  self-explanatory.


---

## MODULE SOURCE: date_overlap.py

```python
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

```
