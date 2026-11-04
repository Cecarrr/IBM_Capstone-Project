# Verified Test Case Generator (tcgen)

A command-line tool that helps you build **trustworthy pytest test files** from
Python docstrings, then measures test quality with mutation testing -- no
guessing, no coverage percentages that lie.

---

## Purpose

tcgen solves two problems:

1. **Prompt generation** -- it assembles a structured LLM prompt from your module
   and three role-layered instruction files, ready to paste into any chat interface.
   The prompt instructs the LLM to derive every expected value from the docstring
   specification, never from running or copying the code.

2. **Quality verification** -- after you save the LLM-generated test file, tcgen
   mutates the module under test one operator at a time and checks whether your
   tests catch the change.  The result is an objective mutation score.

Target users: informatics students and junior developers who need tests they can
actually trust.

---

## Install

Requirements:
- Python 3.10 or later (uses `ast.unparse`, union-type hints)
- `pytest` (the only non-stdlib dependency)

```powershell
pip install pytest
```

No other packages required.  Clone or copy the project directory anywhere; no
`setup.py` or `pyproject.toml` is needed to run the tool.

---

## Workflow

### 1. Build the prompt

```powershell
python tcgen.py build-prompt examples\grade_calculator.py
```

This writes `prompt_out.md` in the current working directory.  The file
contains the three instruction layers followed by your module source in a
fenced code block.

### 2. Paste into any LLM

Open `prompt_out.md`, copy the entire content, and paste it into ChatGPT,
Claude, Gemini, or any other LLM chat.  The tool does **not** call any API;
the LLM step is manual.

### 3. Save the test file

Copy the LLM output and save it as `test_grade_calculator.py` in the same
directory as `grade_calculator.py`.  The test file imports the module by
plain name and can be run directly with pytest.

### 4. Verify the tests

```powershell
python tcgen.py check examples\grade_calculator.py examples\sample_tests\test_grade_calculator_strong.py
```

With a custom timeout (seconds per mutant):

```powershell
python tcgen.py check examples\grade_calculator.py my_tests.py --timeout 15
```

---

## How to read the report

```
============================================================
VERIFIED TEST CASE GENERATOR - Mutation Report
============================================================

[BASELINE] pytest on original source
  exit code  : 0
  collected  : 32
  passed     : 32
  verdict    : PASSED

[CONTROL]  pytest on ast.unparse(original source)
  exit code  : 0
  collected  : 32
  verdict    : PASSED

[MUTANTS]
  total generated : 22
  killed          : 22
  survived        : 0
  timeout (killed): 0
  error (excluded): 0

  mutation score  : 22/22  (100.0%)

  All mutants killed (or errored). No survivors.
============================================================
```

| Section | Meaning |
|---|---|
| BASELINE | Tests run against your original module.  Must PASS before mutations begin. |
| CONTROL  | Tests run against `ast.unparse(module)` -- verifies the unparse round-trip does not change behaviour. |
| killed   | Mutants that caused at least one test to fail (exit code 1). |
| survived | Mutants that passed all tests -- these are the gaps in your test suite. |
| timeout  | Mutants whose subprocess exceeded `--timeout`; counted as killed. |
| error    | Mutants that caused a collection/import error (exit code != 0 and != 1); excluded from the score. |
| score    | `(killed + timeout) / (killed + timeout + survived)`.  100% means every mutant was caught. |

**Surviving mutants** are listed with the original source line and the change
made, so you can see exactly which behaviour is untested:

```
SURVIVING MUTANTS (1) - behaviors not caught by the tests:
------------------------------------------------------------
  [1] line 61: `if score >= 90:`  (comparison op[0] >= -> >)
```

---

## Demo commands (PowerShell)

```powershell
# Build a prompt for any module
python tcgen.py build-prompt "examples\date_overlap.py"

# Run the full verification pipeline
python tcgen.py check "examples\grade_calculator.py" `
    "examples\sample_tests\test_grade_calculator_strong.py"

# Weak tests for contrast
python tcgen.py check "examples\grade_calculator.py" `
    "examples\sample_tests\test_grade_calculator_weak.py"

# Demonstrate that good tests catch a planted bug
python tcgen.py check "examples\buggy\grade_calculator.py" `
    "examples\sample_tests\test_grade_calculator_strong.py"

# Run the tool's own test suite
python -m pytest tests -q

# python -m tcgen also works
python -m tcgen --help
```

---

## Design decisions

### Sandbox imports the mutant

For each mutation the runner creates a fresh `tempfile.TemporaryDirectory`.
It writes the mutated source under the **original module filename**, copies
the test file and all sibling `.py` files from the module's directory, then
invokes pytest with `cwd=sandbox`.  Python's default import mechanism finds
the mutant because it is the only file with that name in `sys.path[0]`.

### Exit-code classification

| pytest exit code | Classification |
|---|---|
| 0 | SURVIVED (all tests passed -- mutant not caught) |
| 1 | KILLED (at least one test failed -- mutant caught) |
| timeout | TIMEOUT (counted as killed) |
| anything else | ERROR (excluded from score) |

A `ZeroDivisionError` raised inside a test causes that test to FAIL, so
pytest exits 1 and the mutant is classified KILLED, not ERROR.

### Baseline gate

Before any mutation, tcgen runs the tests against the original module.  If
any test fails, or zero tests are collected, the run aborts with a clear
message.  This ensures the mutation score is meaningful.

### Unparse control run

After the baseline, tcgen runs the tests against `ast.unparse(ast.parse(source))`.
This catches the rare case where the unparse round-trip changes observable
behaviour (e.g., f-string quirks in older Python versions).  If this run
fails, tcgen aborts and tells you why.

---

## Limitations

- **Only flat sibling `.py` files are copied** into the sandbox.
  Packages (subdirectories with `__init__.py`), data files, and `.pth`
  entries are not handled.  Modules that import from a package in the
  same directory will fail with an import error.

- **Equivalent mutants** can make 100% unreachable.
  A mutant that changes `x + 0` to `x - 0` is semantically identical;
  no test can kill it.  The tool counts it as survived.

- **Operators not mutated** by the current mutator:
  `//` (floor division), `%` (modulo), `**` (power), `in`, `is`,
  `not in`, `is not`.  Unary operators (`-x`, `not x`) are also skipped.

- **Module-level constants and default argument values are mutated.**
  For example, `LIMIT = 100` at module level will produce a
  `constant 100 -> 101` site.  This is intentional but can produce
  false survivors if the constant is only used inside helper functions
  not called by the test.

- **`ast.unparse` drops comments and some whitespace.**
  The control run uses the unparsed source.  If the module under test
  contains type-ignore comments (`# type: ignore`) or pragma comments
  relied on by other tools, those are lost after unparsing.

- **Mutation score does not prove correctness.**
  A 100% mutation score means every mutant generated by these six operator
  families was caught.  It does not mean the tests are logically complete,
  that the specification is correct, or that the code has no other bugs.

---

## Prompt iteration log

*(Fill in your LLM session notes here.)*

---

## Notes on examples/

- `examples/grade_calculator.py`, `examples/password_checker.py`,
  `examples/date_overlap.py` -- three small, self-contained stdlib-only
  modules with precise docstrings.

- `examples/sample_tests/test_grade_calculator_strong.py` and
  `test_grade_calculator_weak.py` are **hand-written reference tests, not
  agent output**.  They demonstrate what a strong vs. weak test suite looks
  like before running `check`.

- `examples/buggy/` contains copies of each module with exactly one planted
  bug.  See `examples/buggy/BUGS.md` for details.

- The LLM step is manual -- no API key is required or used.
