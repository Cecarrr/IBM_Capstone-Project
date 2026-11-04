"""
tcgen.runner
============
Thin wrapper around a pytest subprocess.

Uses sys.executable (the current interpreter) to invoke pytest so that the
sandboxed subprocess sees the same site-packages, including pytest itself.

Every pytest run is performed in an isolated temporary directory containing:
  - The module under test (written under its original filename)
  - The test file
  - All sibling .py files from the module's original directory

Environment flags set for every subprocess:
  PYTHONDONTWRITEBYTECODE=1  -- no .pyc accumulation in the sandbox
  PYTHONUTF8=1               -- UTF-8 mode for all I/O
  PYTHONIOENCODING=utf-8     -- belt-and-suspenders for Windows cp1252 terminals

Exit-code classification (per approved plan):
  0  -> SURVIVED
  1  -> KILLED
  timeout -> TIMEOUT  (counted as killed)
  other   -> ERROR    (excluded from score)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Classification(Enum):
    KILLED   = "killed"
    SURVIVED = "survived"
    TIMEOUT  = "timeout"
    ERROR    = "error"


@dataclass
class RunResult:
    """Raw outcome of a single pytest invocation."""
    exit_code: int
    passed: int
    failed: int
    collected: int
    raw_output: str
    timed_out: bool = False
    classification: Classification = field(init=False)

    def __post_init__(self) -> None:
        if self.timed_out:
            self.classification = Classification.TIMEOUT
        elif self.exit_code == 0:
            self.classification = Classification.SURVIVED
        elif self.exit_code == 1:
            self.classification = Classification.KILLED
        else:
            self.classification = Classification.ERROR


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------

# Matches "collected N item(s)"
_COLLECTED_RE = re.compile(r"collected\s+(\d+)\s+item", re.IGNORECASE)
# pytest exit code 5 means "no tests collected"
_NO_TESTS_EXIT = 5


def _parse_counts(output: str) -> tuple[int, int, int]:
    """Return (passed, failed, collected) parsed from pytest stdout."""
    passed = failed = collected = 0

    for line in output.splitlines():
        m = _COLLECTED_RE.search(line)
        if m:
            collected = int(m.group(1))

    # The short-test-summary line ends with "=== N passed ... ==="
    for line in reversed(output.splitlines()):
        if "passed" in line or "failed" in line or "error" in line:
            # Extract all "N <word>" pairs
            for count, word in re.findall(r"(\d+)\s+(passed|failed|error)", line):
                if word == "passed":
                    passed = int(count)
                elif word in ("failed", "error"):
                    failed += int(count)
            break

    # With -q the "collected N items" line is suppressed.
    # Fall back to passed + failed as the lower-bound collection count.
    if collected == 0:
        collected = passed + failed
    return passed, failed, collected


# ---------------------------------------------------------------------------
# Sandbox helpers
# ---------------------------------------------------------------------------

def _build_sandbox(
    module_source: str,
    module_filename: str,
    module_dir: Path,
    test_path: Path,
) -> tempfile.TemporaryDirectory:
    """Create a temporary directory containing everything pytest needs.

    Contents:
      <module_filename>       — the source to run against (may be mutated)
      <test_path.name>        — copy of the test file
      <all other *.py files>  — copies of sibling modules (excluding module itself)

    Returns the TemporaryDirectory object; the caller is responsible for cleanup.
    """
    tmpdir = tempfile.TemporaryDirectory(prefix="tcgen_", ignore_cleanup_errors=True)
    tmp = Path(tmpdir.name)

    # Write the module source (original or mutated).
    (tmp / module_filename).write_text(module_source, encoding="utf-8")

    # Copy the test file.
    shutil.copy2(test_path, tmp / test_path.name)

    # Copy sibling .py files (skip the module itself — already written above).
    for sibling in module_dir.glob("*.py"):
        if sibling.name != module_filename and sibling.name != test_path.name:
            shutil.copy2(sibling, tmp / sibling.name)

    return tmpdir


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_PYTEST_FLAGS = ["-x", "-q", "-p", "no:cacheprovider"]


def run_pytest(
    test_filename: str,
    cwd: Path,
    timeout: float,
) -> RunResult:
    """Run pytest on *test_filename* inside *cwd*.

    Parameters
    ----------
    test_filename:
        Just the filename (no directory) of the test file inside *cwd*.
    cwd:
        The directory in which pytest is invoked (the sandbox).
    timeout:
        Maximum wall-clock seconds for the subprocess.  On expiry the process
        is killed (SIGKILL on POSIX, TerminateProcess on Windows) and a
        TIMEOUT result is returned.

    Returns
    -------
    RunResult
        Parsed outcome.  .classification is set by __post_init__ or overridden
        to TIMEOUT when the process times out.
    """
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *_PYTEST_FLAGS, test_filename],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        # Kill is handled by subprocess on TimeoutExpired; stdout/stderr may
        # be partial bytes or str depending on Python version.
        raw = ""
        if exc.stdout:
            raw += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", errors="replace")
        if exc.stderr:
            raw += exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", errors="replace")
        return RunResult(
            exit_code=-1,
            passed=0,
            failed=0,
            collected=0,
            raw_output=raw,
            timed_out=True,
        )

    raw = proc.stdout + proc.stderr
    passed, failed, collected = _parse_counts(raw)

    # pytest exit 5 = no tests collected; treat collected as 0.
    if proc.returncode == _NO_TESTS_EXIT:
        collected = 0

    result = RunResult(
        exit_code=proc.returncode,
        passed=passed,
        failed=failed,
        collected=collected,
        raw_output=raw,
    )
    return result


def run_in_sandbox(
    module_source: str,
    module_filename: str,
    module_dir: Path,
    test_path: Path,
    timeout: float,
) -> RunResult:
    """Create a sandbox, run pytest, clean up, and return the result.

    This is the high-level helper used for both baseline and mutant runs.
    The sandbox directory is always removed even if pytest crashes.
    """
    tmpdir = _build_sandbox(module_source, module_filename, module_dir, test_path)
    try:
        return run_pytest(
            test_filename=test_path.name,
            cwd=Path(tmpdir.name),
            timeout=timeout,
        )
    finally:
        tmpdir.cleanup()
