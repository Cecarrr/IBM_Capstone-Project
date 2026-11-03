# Planted bugs in examples/buggy/

Each file in this directory is an exact copy of the corresponding file in examples/,
except for one deliberately planted bug.  The docstrings are unchanged so that the
tool can generate tests from the specification and then demonstrate that those tests
catch the regression.

---

## grade_calculator.py

**Bug:** The boundary condition for "A" uses strict greater-than (`> 90`) instead of
greater-than-or-equal (`>= 90`).

**Effect:** `score_to_grade(90)` returns `"B"` instead of `"A"`.

**Expected failing test:** any test that asserts `score_to_grade(90) == "A"` will FAIL
on the buggy version.  A test suite that only checks midpoints (e.g., score 95) will
miss this bug.

---

## password_checker.py

**Bug:** The weak-password threshold uses `<=` instead of `<`, so a password of
exactly 8 characters is classified as "weak" instead of "medium".

**Effect:** `check_strength("abcdefgh")` (length 8) returns `"weak"` instead of
`"medium"`.

**Expected failing test:** any test that asserts `check_strength("abcdefgh") == "medium"`
will FAIL on the buggy version.

---

## date_overlap.py

**Bug:** The overlap condition uses strict less-than (`<`) instead of
less-than-or-equal (`<=`), so two ranges that share exactly one endpoint day are
reported as NOT overlapping.

**Effect:** `ranges_overlap(date(2024,1,1), date(2024,1,5), date(2024,1,5), date(2024,1,10))`
returns `False` instead of `True`.

**Expected failing test:** any test that asserts ranges touching on exactly one day
overlap will FAIL on the buggy version.
