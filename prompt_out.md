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

## MODULE SOURCE: password_checker.py

```python
"""
password_checker.py
===================
Function for assessing the strength of a password string.
"""


def check_strength(password: str) -> str:
    """Return the strength of a password as "weak", "medium", or "strong".

    Classification rules (applied in this order):
      1. "weak"   -- the password is strictly shorter than 8 characters
                     (i.e., length 0 through 7 inclusive gives "weak").
      2. "strong" -- the password is at least 12 characters long AND satisfies
                     ALL FOUR of the following character-class requirements:
                       - at least one lowercase ASCII letter (a-z)
                       - at least one uppercase ASCII letter (A-Z)
                       - at least one ASCII digit (0-9)
                       - at least one symbol, defined as any printable non-alphanumeric
                         ASCII character (i.e., any character in string.punctuation,
                         for example: ! @ # $ % ^ & * ( ) - _ = + etc.)
                     A password of exactly 12 characters that meets all four requirements
                     is "strong".  Length alone (>= 12) is not sufficient.
      3. "medium" -- every password that is not "weak" and not "strong".
                     This includes passwords of length 8 to 11, and passwords of
                     length >= 12 that are missing one or more character classes.

    Parameters
    ----------
    password : str
        The password string to evaluate.

    Returns
    -------
    str
        One of "weak", "medium", or "strong".

    Raises
    ------
    TypeError
        If ``password`` is not a str.

    Examples
    --------
    >>> check_strength("abc")
    'weak'
    >>> check_strength("abcdefgh")
    'medium'
    >>> check_strength("Abcdefgh1!")
    'medium'
    >>> check_strength("Abcdefgh12!")
    'strong'
    >>> check_strength("")
    'weak'
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be a str, got {type(password).__name__}")

    if len(password) < 8:
        return "weak"

    if len(password) >= 12:
        has_lower  = any(c.islower() for c in password)
        has_upper  = any(c.isupper() for c in password)
        has_digit  = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() and c.isprintable() for c in password)
        if has_lower and has_upper and has_digit and has_symbol:
            return "strong"

    return "medium"

```
