"""
tests/test_runner.py
====================
Tests for tcgen.runner using REAL pytest subprocesses.

No mocking. All tests are deterministic (no network, no randomness).
Uses tmp_path (pytest fixture) for all file I/O.
"""
import glob as _glob
import os
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tcgen.runner import (
    Classification,
    RunResult,
    _build_sandbox,
    _parse_counts,
    run_in_sandbox,
    run_pytest,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, text: str) -> Path:
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# C2-a: _parse_counts from real pytest output patterns
# ---------------------------------------------------------------------------

def test_parse_counts_all_pass():
    output = "3 passed in 0.05s\n"
    passed, failed, collected = _parse_counts(output)
    assert passed == 3
    assert failed == 0
    assert collected == 3   # fallback from passed+failed


def test_parse_counts_one_fail():
    output = "2 passed, 1 failed in 0.10s\n"
    passed, failed, collected = _parse_counts(output)
    assert passed == 2
    assert failed == 1


def test_parse_counts_collection_error():
    # pytest exit 2 or 4 with "error" in summary
    output = "1 error in 0.01s\n"
    passed, failed, collected = _parse_counts(output)
    assert failed == 1   # "error" counted as failed


def test_parse_counts_no_tests():
    output = ""
    passed, failed, collected = _parse_counts(output)
    assert passed == 0
    assert failed == 0
    assert collected == 0


# ---------------------------------------------------------------------------
# C2-b: exit-code classification
# ---------------------------------------------------------------------------

def test_classification_exit_0_survived():
    r = RunResult(exit_code=0, passed=1, failed=0, collected=1, raw_output="")
    assert r.classification == Classification.SURVIVED


def test_classification_exit_1_killed():
    r = RunResult(exit_code=1, passed=0, failed=1, collected=1, raw_output="")
    assert r.classification == Classification.KILLED


def test_classification_exit_2_error():
    r = RunResult(exit_code=2, passed=0, failed=0, collected=0, raw_output="")
    assert r.classification == Classification.ERROR


def test_real_empty_test_file_exit_5(tmp_path: Path):
    """A real run of an empty test file: pytest exits 5, collected==0, ERROR."""
    mod  = _write(tmp_path / "mod.py", "def f(): return 1\n")
    test = _write(tmp_path / "test_empty.py", "# no tests here\n")
    result = run_in_sandbox(
        module_source=mod.read_text(encoding="utf-8"),
        module_filename="mod.py",
        module_dir=tmp_path,
        test_path=test,
        timeout=10.0,
    )
    assert result.exit_code == 5, \
        f"Expected exit code 5 for empty test file, got {result.exit_code}"
    assert result.collected == 0, \
        f"Expected collected==0 for empty test file, got {result.collected}"
    assert result.classification == Classification.ERROR


def test_classification_timed_out():
    r = RunResult(exit_code=-1, passed=0, failed=0, collected=0,
                  raw_output="", timed_out=True)
    assert r.classification == Classification.TIMEOUT


# ---------------------------------------------------------------------------
# C2-c: KEY REGRESSION -- sandbox imports the MUTATED module
# ---------------------------------------------------------------------------

def test_sandbox_imports_mutated_module(tmp_path: Path):
    """A module returning 1 vs a mutant returning 2 must make the test fail."""
    mod = _write(tmp_path / "mymod.py", """\
        def get_value():
            return 1
    """)
    test = _write(tmp_path / "test_mymod.py", """\
        from mymod import get_value
        def test_value():
            assert get_value() == 1
    """)
    # Original passes
    r_orig = run_in_sandbox(
        module_source=mod.read_text(encoding="utf-8"),
        module_filename="mymod.py",
        module_dir=tmp_path,
        test_path=test,
        timeout=10.0,
    )
    assert r_orig.classification == Classification.SURVIVED

    # Mutant (returns 2) must fail
    mutant_src = "def get_value():\n    return 2\n"
    r_mut = run_in_sandbox(
        module_source=mutant_src,
        module_filename="mymod.py",
        module_dir=tmp_path,
        test_path=test,
        timeout=10.0,
    )
    assert r_mut.classification == Classification.KILLED


# ---------------------------------------------------------------------------
# C2-d: timeout kills the process; no tcgen_* temp directory is left
# ---------------------------------------------------------------------------

def test_timeout_kills_and_no_temp_dir_leaked(tmp_path: Path):
    mod = _write(tmp_path / "loopy.py", "def f(): return 1\n")
    test = _write(tmp_path / "test_loopy.py", """\
        from loopy import f
        def test_hang():
            while True:
                pass
    """)
    import time
    start = time.monotonic()
    result = run_in_sandbox(
        module_source=mod.read_text(encoding="utf-8"),
        module_filename="loopy.py",
        module_dir=tmp_path,
        test_path=test,
        timeout=2.0,
    )
    elapsed = time.monotonic() - start
    assert result.timed_out, "Expected timed_out=True"
    assert result.classification == Classification.TIMEOUT
    # Subprocess must have been killed within a reasonable window
    assert elapsed < 6.0, f"Took too long: {elapsed:.1f}s"
    # No tcgen_ temp directories should remain after cleanup
    leftovers = _glob.glob(os.path.join(tempfile.gettempdir(), "tcgen_*"))
    assert leftovers == [], f"Temp dirs left: {leftovers}"


# ---------------------------------------------------------------------------
# C2-e: module and test file in different directories
# ---------------------------------------------------------------------------

def test_module_and_test_in_different_dirs(tmp_path: Path):
    mod_dir = tmp_path / "src"
    test_dir = tmp_path / "tests"
    mod_dir.mkdir(); test_dir.mkdir()

    mod = _write(mod_dir / "calc.py", """\
        def add(a, b):
            return a + b
    """)
    test = _write(test_dir / "test_calc.py", """\
        from calc import add
        def test_add():
            assert add(1, 2) == 3
    """)
    result = run_in_sandbox(
        module_source=mod.read_text(encoding="utf-8"),
        module_filename="calc.py",
        module_dir=mod_dir,
        test_path=test,
        timeout=10.0,
    )
    assert result.classification == Classification.SURVIVED


# ---------------------------------------------------------------------------
# C2-f: sibling .py files are copied into the sandbox
# ---------------------------------------------------------------------------

def test_sibling_files_copied(tmp_path: Path):
    _write(tmp_path / "helper.py", "VALUE = 99\n")
    mod = _write(tmp_path / "main.py", """\
        from helper import VALUE
        def get():
            return VALUE
    """)
    test = _write(tmp_path / "test_main.py", """\
        from main import get
        def test_get():
            assert get() == 99
    """)
    result = run_in_sandbox(
        module_source=mod.read_text(encoding="utf-8"),
        module_filename="main.py",
        module_dir=tmp_path,
        test_path=test,
        timeout=10.0,
    )
    assert result.classification == Classification.SURVIVED


# ---------------------------------------------------------------------------
# C2-g: path containing spaces works
# ---------------------------------------------------------------------------

def test_path_with_spaces(tmp_path: Path):
    spaced = tmp_path / "my module dir"
    spaced.mkdir()
    mod = _write(spaced / "spacey.py", "def f(): return 7\n")
    test = _write(spaced / "test_spacey.py", """\
        from spacey import f
        def test_f():
            assert f() == 7
    """)
    result = run_in_sandbox(
        module_source=mod.read_text(encoding="utf-8"),
        module_filename="spacey.py",
        module_dir=spaced,
        test_path=test,
        timeout=10.0,
    )
    assert result.classification == Classification.SURVIVED


# ---------------------------------------------------------------------------
# C2-h: module with non-ASCII characters (e-acute in a string)
# ---------------------------------------------------------------------------

def test_non_ascii_module(tmp_path: Path):
    mod_src = "def greet():\n    return 'caf\u00e9'\n"
    mod = tmp_path / "nonascii.py"
    mod.write_text(mod_src, encoding="utf-8")
    test = _write(tmp_path / "test_nonascii.py", """\
        from nonascii import greet
        def test_greet():
            assert greet() == 'caf\\u00e9'
    """)
    result = run_in_sandbox(
        module_source=mod_src,
        module_filename="nonascii.py",
        module_dir=tmp_path,
        test_path=test,
        timeout=10.0,
    )
    assert result.classification == Classification.SURVIVED


# ---------------------------------------------------------------------------
# Real run: 2 passing tests + 1 failing test (-x stops at first failure)
# ---------------------------------------------------------------------------

def test_real_two_pass_one_fail(tmp_path: Path):
    """A real run with 2 passing tests and 1 failing test.

    With -x, pytest stops at the first failure, so:
      exit_code == 1, failed >= 1, passed is parsed from the summary line.
    """
    mod = _write(tmp_path / "calc.py", """\
        def add(a, b):
            return a + b
    """)
    # Two tests pass, one fails (wrong expected value).
    # -x stops at the first failure, so we get 1 failed + however many passed before it.
    # Order: pass, pass, fail -> with -x we see 2 passed, 1 failed.
    test = _write(tmp_path / "test_calc.py", """\
        from calc import add
        def test_one():
            assert add(1, 2) == 3
        def test_two():
            assert add(0, 0) == 0
        def test_three_fails():
            assert add(1, 1) == 99   # intentionally wrong
    """)
    result = run_in_sandbox(
        module_source=mod.read_text(encoding="utf-8"),
        module_filename="calc.py",
        module_dir=tmp_path,
        test_path=test,
        timeout=10.0,
    )
    assert result.exit_code == 1, \
        f"Expected exit code 1, got {result.exit_code}\nOutput:\n{result.raw_output}"
    assert result.failed >= 1, \
        f"Expected at least 1 failed test, got {result.failed}\nOutput:\n{result.raw_output}"
    assert result.passed == 2, \
        f"Expected 2 passed tests, got {result.passed}\nOutput:\n{result.raw_output}"
    assert result.classification == Classification.KILLED
