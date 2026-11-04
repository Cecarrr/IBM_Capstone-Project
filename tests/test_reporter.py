"""
tests/test_reporter.py
======================
Tests for tcgen.reporter.build_report.

All assertions operate on the returned string; no stdout capturing needed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tcgen.mutator import MutationSite, Mutant
from tcgen.reporter import MutantResult, build_report
from tcgen.runner import Classification, RunResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run(exit_code: int = 0, passed: int = 1, failed: int = 0,
              collected: int = 1, timed_out: bool = False) -> RunResult:
    return RunResult(
        exit_code=exit_code,
        passed=passed,
        failed=failed,
        collected=collected,
        raw_output="",
        timed_out=timed_out,
    )


def _make_site(index: int = 0, lineno: int = 1,
               description: str = "arithmetic + -> -",
               source_line: str = "return a + b") -> MutationSite:
    return MutationSite(
        index=index,
        lineno=lineno,
        col_offset=0,
        description=description,
        _source_line=source_line,
    )


def _make_mutant(index: int = 0, description: str = "arithmetic + -> -",
                 source_line: str = "return a + b") -> Mutant:
    return Mutant(
        site=_make_site(index, description=description, source_line=source_line),
        mutated_source="def f(): return 0",
    )


def _make_result(cls: Classification, exit_code: int = 0,
                 index: int = 0, description: str = "arithmetic + -> -",
                 source_line: str = "return a + b") -> MutantResult:
    return MutantResult(
        mutant=_make_mutant(index, description=description, source_line=source_line),
        classification=cls,
        exit_code=exit_code,
    )


# ---------------------------------------------------------------------------
# C3-a: 1 killed + 1 timeout + 1 survived -> score 2/3 (66.7%)
# ---------------------------------------------------------------------------

def test_score_killed_plus_timeout_over_total():
    baseline = _make_run()
    control  = _make_run()
    results = [
        _make_result(Classification.KILLED,   exit_code=1, index=0),
        _make_result(Classification.TIMEOUT,  exit_code=-1, index=1),
        _make_result(Classification.SURVIVED, exit_code=0, index=2),
    ]
    report = build_report(baseline, control, results)
    assert "2/3" in report
    assert "66.7%" in report


# ---------------------------------------------------------------------------
# C3-b: N/A when 0 mutants
# ---------------------------------------------------------------------------

def test_score_na_no_mutants():
    report = build_report(_make_run(), _make_run(), [])
    assert "N/A" in report
    assert "no mutation sites found" in report


# ---------------------------------------------------------------------------
# C3-c: N/A when all errored
# ---------------------------------------------------------------------------

def test_score_na_all_errors():
    results = [
        _make_result(Classification.ERROR, exit_code=2, index=0),
        _make_result(Classification.ERROR, exit_code=2, index=1),
    ]
    report = build_report(_make_run(), _make_run(), results)
    assert "N/A" in report
    assert "errored" in report


# ---------------------------------------------------------------------------
# C3-d: baseline verdict labels
# ---------------------------------------------------------------------------

def test_verdict_passed():
    report = build_report(_make_run(exit_code=0), _make_run(), [])
    assert "PASSED" in report


def test_verdict_failed():
    baseline = _make_run(exit_code=1)
    # build_report doesn't abort; caller does -- just verify the label
    report = build_report(baseline, _make_run(), [])
    assert "FAILED" in report


def test_verdict_timed_out():
    baseline = _make_run(exit_code=-1, timed_out=True)
    report = build_report(baseline, _make_run(), [])
    assert "TIMED OUT" in report


# ---------------------------------------------------------------------------
# C3-e: ERROR section prints numeric exit code
# ---------------------------------------------------------------------------

def test_error_section_prints_numeric_exit_code():
    results = [_make_result(Classification.ERROR, exit_code=2, index=0)]
    report = build_report(_make_run(), _make_run(), results)
    assert "exit code 2" in report


# ---------------------------------------------------------------------------
# C3-f: survivors show the original source line
# ---------------------------------------------------------------------------

def test_survivors_show_source_line():
    results = [
        _make_result(Classification.SURVIVED, exit_code=0, index=0,
                     source_line="    if score >= 90:")
    ]
    report = build_report(_make_run(), _make_run(), results)
    assert "if score >= 90:" in report


# ---------------------------------------------------------------------------
# C3-g: entire report is ASCII-only
# ---------------------------------------------------------------------------

def test_report_is_ascii():
    results = [
        _make_result(Classification.SURVIVED, index=0,
                     description="comparison op[0] >= -> >",
                     source_line="if score >= 90:"),
        _make_result(Classification.KILLED, exit_code=1, index=1),
        _make_result(Classification.TIMEOUT, exit_code=-1, index=2),
        _make_result(Classification.ERROR, exit_code=2, index=3),
    ]
    report = build_report(_make_run(), _make_run(), results)
    assert report.isascii(), f"Non-ASCII chars in report: {[c for c in report if not c.isascii()]}"
