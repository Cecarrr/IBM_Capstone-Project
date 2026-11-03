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
