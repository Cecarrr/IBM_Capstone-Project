"""
tests/test_cli.py
=================
Integration tests for the tcgen CLI.

Runs `python tcgen.py ...` and `python -m tcgen ...` as subprocesses
so the full argument-parsing and pipeline paths are exercised.
No mocking.
"""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT    = Path(__file__).parent.parent
TCGEN  = str(ROOT / "tcgen.py")   # absolute path to the CLI entry point


def _run(*args, cwd=None):
    """Run a CLI command and return (returncode, stdout+stderr).

    Always uses the absolute path to tcgen.py so the script is found
    regardless of the working directory.
    """
    result = subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=_env(),
    )
    return result.returncode, result.stdout + result.stderr


def _env():
    import os
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    # Ensure the project root is on PYTHONPATH so `python -m tcgen` finds the package.
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + existing if existing else "")
    return env


def _write(path: Path, text: str) -> Path:
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# C4-a: build-prompt output order: Layer 1, 2, 3, then source fence
# ---------------------------------------------------------------------------

def test_build_prompt_layer_order(tmp_path: Path):
    mod = _write(tmp_path / "simple.py", """\
        def add(a, b):
            \"\"\"Return a + b.\"\"\"
            return a + b
    """)
    rc, out = _run(TCGEN, "build-prompt", str(mod), cwd=tmp_path)
    assert rc == 0, f"build-prompt failed:\n{out}"

    # prompt_out.md written in tmp_path (CWD)
    prompt = (tmp_path / "prompt_out.md").read_text(encoding="utf-8")
    # Search for the section headings (the H1 lines that open each layer file)
    import re as _re
    # Find the positions of the top-level headings (lines starting with "# Layer N")
    matches = {m.group(1): m.start() for m in _re.finditer(r"^# Layer (\d)", prompt, _re.MULTILINE)}
    assert set(matches.keys()) >= {"1", "2", "3"}, f"Missing layer headers: {matches}"
    pos_src = prompt.find("MODULE SOURCE")
    assert matches["1"] < matches["2"] < matches["3"] < pos_src, \
        f"Layers not in order: {matches}, SOURCE at {pos_src}"


# ---------------------------------------------------------------------------
# C4-b: source containing ``` is wrapped in a longer fence
# ---------------------------------------------------------------------------

def test_build_prompt_backtick_fence(tmp_path: Path):
    # Write a module whose docstring literally contains ``` so the fence must be extended.
    backtick3 = "```"
    source = (
        "def f():\n"
        "    '''\n"
        "    Example::\n\n"
        f"        {backtick3}python\n"
        "        f()\n"
        f"        {backtick3}\n"
        "    '''\n"
        "    return 1\n"
    )
    mod = tmp_path / "docmod.py"
    mod.write_text(source, encoding="utf-8")
    rc, out = _run(TCGEN, "build-prompt", str(mod), cwd=tmp_path)
    assert rc == 0, f"build-prompt failed: {out}"
    prompt = (tmp_path / "prompt_out.md").read_text(encoding="utf-8")
    # The MODULE SOURCE section must use a fence of at least 4 backticks
    # (one more than the 3 backticks present in the source).
    import re
    b = "`"
    pat = r"^(" + b + r"{3,})python$"
    fences = re.findall(pat, prompt, re.MULTILINE)
    assert fences, "No opening code fence found in prompt_out.md"
    max_fence = max(len(f) for f in fences)
    assert max_fence >= 4, \
        f"No fence extended beyond 3 backticks; fences found: {fences}"


# ---------------------------------------------------------------------------
# C4-c: missing file gives exit 1 with one clear error message
# ---------------------------------------------------------------------------

def test_build_prompt_missing_file():
    rc, out = _run(TCGEN, "build-prompt", "does_not_exist.py")
    assert rc == 1
    assert "error" in out.lower()
    assert out.count("\n") < 5, "Error message unexpectedly long"


# ---------------------------------------------------------------------------
# C4-d: syntax error gives exit 1 with one clear message
# ---------------------------------------------------------------------------

def test_build_prompt_syntax_error(tmp_path: Path):
    bad = _write(tmp_path / "bad.py", "def f(\n")
    rc, out = _run(TCGEN, "build-prompt", str(bad), cwd=tmp_path)
    assert rc == 1
    assert "error" in out.lower()
    # Must not print a Python traceback
    assert "Traceback" not in out


# ---------------------------------------------------------------------------
# C4-e: python -m tcgen build-prompt works
# ---------------------------------------------------------------------------

def test_m_tcgen_build_prompt(tmp_path: Path):
    mod = _write(tmp_path / "m.py", "def f(): return 1\n")
    rc, out = _run("-m", "tcgen", "build-prompt", str(mod), cwd=tmp_path)
    assert rc == 0, f"python -m tcgen failed:\n{out}"
    assert (tmp_path / "prompt_out.md").exists()


# ---------------------------------------------------------------------------
# C4-f: check aborts when tests fail on original code
# ---------------------------------------------------------------------------

def test_check_aborts_on_failing_baseline(tmp_path: Path):
    mod = _write(tmp_path / "buggy.py", """\
        def add(a, b):
            return a - b   # wrong
    """)
    test = _write(tmp_path / "test_buggy.py", """\
        from buggy import add
        def test_add():
            assert add(1, 2) == 3
    """)
    rc, out = _run(TCGEN, "check", str(mod), str(test))
    assert rc == 1
    lower = out.lower()
    assert "fail" in lower or "error" in lower


# ---------------------------------------------------------------------------
# C4-g: check aborts when 0 tests are collected
# ---------------------------------------------------------------------------

def test_check_aborts_on_zero_tests(tmp_path: Path):
    mod = _write(tmp_path / "mod.py", "def f(): return 1\n")
    test = _write(tmp_path / "test_empty.py", "# no tests here\n")
    rc, out = _run(TCGEN, "check", str(mod), str(test))
    assert rc == 1
    assert "pytest collected 0 tests" in out, \
        f"Expected exact message 'pytest collected 0 tests' in output:\n{out}"


# ---------------------------------------------------------------------------
# C4-h: build-prompt works from a different CWD (project root still found)
# ---------------------------------------------------------------------------

def test_build_prompt_from_different_cwd(tmp_path: Path):
    other = tmp_path / "other_dir"
    other.mkdir()
    mod = _write(other / "thing.py", "def f(): return 42\n")
    # Run from `other` dir, pass absolute path to module
    rc, out = _run(TCGEN, "build-prompt", str(mod), cwd=other)
    assert rc == 0
    # prompt_out.md should be in `other` (CWD)
    assert (other / "prompt_out.md").exists()


# ---------------------------------------------------------------------------
# End-to-end: check on grade_calculator with strong and weak suites
# ---------------------------------------------------------------------------

def test_check_grade_calculator_strong_suite():
    """Full end-to-end: strong suite scores 100% on the good module."""
    rc, out = _run(
        TCGEN, "check",
        str(ROOT / "examples" / "grade_calculator.py"),
        str(ROOT / "examples" / "sample_tests" / "test_grade_calculator_strong.py"),
    )
    assert rc == 0, f"Expected exit 0, got {rc}.\nOutput:\n{out}"
    assert "22/22" in out, f"Expected '22/22' in output:\n{out}"
    assert "100.0%" in out, f"Expected '100.0%' in output:\n{out}"


def test_check_grade_calculator_weak_suite():
    """Full end-to-end: weak suite has surviving mutants and scores below 50%."""
    rc, out = _run(
        TCGEN, "check",
        str(ROOT / "examples" / "grade_calculator.py"),
        str(ROOT / "examples" / "sample_tests" / "test_grade_calculator_weak.py"),
    )
    assert rc == 0, f"Expected exit 0, got {rc}.\nOutput:\n{out}"
    assert "survived" in out.lower(), \
        f"Expected surviving mutants listed in output:\n{out}"
    # Score must be below 50%: extract the percentage from "N/M  (X.X%)"
    import re
    m = re.search(r"\((\d+\.\d+)%\)", out)
    assert m is not None, f"Could not find score percentage in output:\n{out}"
    score = float(m.group(1))
    assert score < 50.0, f"Weak suite score {score:.1f}% is not below 50%"
