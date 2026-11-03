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
