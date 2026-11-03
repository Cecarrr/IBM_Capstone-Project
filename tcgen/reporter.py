"""
tcgen.reporter
==============
Formats and prints the mutation testing report.

The report covers:
  1. Baseline run results (pass/fail on the original code).
  2. Mutant statistics: killed, survived, timeout, error counts.
  3. Mutation score = killed / (killed + survived).
     - "N/A" when killed + survived == 0 (all errors).
  4. Per-surviving-mutant details: original line number + change description.
  5. Per-error-mutant details (excluded from score).

The public function also returns the report as a plain string so that
tests can assert on it without capturing stdout.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tcgen.mutator import Mutant
    from tcgen.runner import Classification, RunResult


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class MutantResult:
    """Outcome for a single mutant."""
    mutant: "Mutant"
    classification: "Classification"
    exit_code: int = 0   # real pytest exit code (or -1 for timeout)


def _safe(text: str) -> str:
    """Return *text* with non-ASCII characters replaced by '?' for safe terminal output."""
    return text.encode("ascii", "replace").decode("ascii")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

_SEP  = "=" * 60
_SEP2 = "-" * 60


def _fmt_run(result: "RunResult", *, is_baseline: bool = False) -> str:
    """Format a RunResult for the baseline/control section.

    Uses PASSED / FAILED labels (not the mutant-specific SURVIVED/KILLED labels).
    """
    from tcgen.runner import Classification
    if result.timed_out:
        verdict = "TIMED OUT"
    elif result.exit_code == 0:
        verdict = "PASSED"
    else:
        verdict = "FAILED"
    return (
        f"  exit code  : {result.exit_code}\n"
        f"  collected  : {result.collected}\n"
        f"  passed     : {result.passed}\n"
        f"  failed     : {result.failed}\n"
        f"  verdict    : {verdict}"
    )


def build_report(
    baseline: "RunResult",
    control: "RunResult",
    results: list[MutantResult],
) -> str:
    """Build and return the full report string.

    Parameters
    ----------
    baseline:
        RunResult from running pytest against the original source.
    control:
        RunResult from running pytest against ast.unparse(original source).
        Must pass; if it fails the caller should abort before reaching here.
    results:
        One MutantResult per mutation site, in site order.
    """
    from tcgen.runner import Classification  # local import to avoid circular

    lines: list[str] = []

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    lines.append(_SEP)
    lines.append("VERIFIED TEST CASE GENERATOR - Mutation Report")
    lines.append(_SEP)

    # ------------------------------------------------------------------
    # Baseline
    # ------------------------------------------------------------------
    lines.append("\n[BASELINE] pytest on original source")
    lines.append(_fmt_run(baseline))

    lines.append("\n[CONTROL]  pytest on ast.unparse(original source)")
    lines.append(_fmt_run(control))

    # ------------------------------------------------------------------
    # Mutant counts
    # ------------------------------------------------------------------
    killed   = sum(1 for r in results if r.classification == Classification.KILLED)
    survived = sum(1 for r in results if r.classification == Classification.SURVIVED)
    timeouts = sum(1 for r in results if r.classification == Classification.TIMEOUT)
    errors   = sum(1 for r in results if r.classification == Classification.ERROR)
    total    = len(results)

    lines.append(f"\n[MUTANTS]")
    lines.append(f"  total generated : {total}")
    lines.append(f"  killed          : {killed}")
    lines.append(f"  survived        : {survived}")
    lines.append(f"  timeout (killed): {timeouts}")
    lines.append(f"  error (excluded): {errors}")

    # ------------------------------------------------------------------
    # Score  (timeouts count as killed)
    # ------------------------------------------------------------------
    effective_killed = killed + timeouts
    denominator = effective_killed + survived
    if total == 0:
        score_str = "N/A  (no mutation sites found)"
    elif denominator == 0:
        score_str = "N/A  (all mutants errored - check import/collection errors)"
    else:
        pct = effective_killed / denominator * 100
        score_str = f"{effective_killed}/{denominator}  ({pct:.1f}%)"

    lines.append(f"\n  mutation score  : {score_str}")

    # ------------------------------------------------------------------
    # Surviving mutants
    # ------------------------------------------------------------------
    survivors = [r for r in results if r.classification == Classification.SURVIVED]
    if survivors:
        lines.append(f"\n{_SEP2}")
        lines.append(f"SURVIVING MUTANTS ({len(survivors)}) - behaviors not caught by the tests:")
        lines.append(_SEP2)
        for i, r in enumerate(survivors, 1):
            s = r.mutant.site
            src_line = _safe(r.mutant.site._source_line)
            lines.append(
                f"  [{i}] line {s.lineno}: `{src_line}`  ({_safe(s.description)})"
            )
    else:
        lines.append("\n  All mutants killed (or errored). No survivors.")

    # ------------------------------------------------------------------
    # Error mutants
    # ------------------------------------------------------------------
    error_mutants = [r for r in results if r.classification == Classification.ERROR]
    if error_mutants:
        lines.append(f"\n{_SEP2}")
        lines.append(f"ERROR MUTANTS ({len(error_mutants)}) - excluded from score:")
        lines.append(_SEP2)
        for r in error_mutants:
            s = r.mutant.site
            lines.append(f"  line {s.lineno}  {_safe(s.description)}  (exit code {r.exit_code})")

    lines.append(f"\n{_SEP}")

    return "\n".join(lines)


def print_report(
    baseline: "RunResult",
    control: "RunResult",
    results: list[MutantResult],
) -> str:
    """Build the report, print it to stdout, and return it."""
    report = build_report(baseline, control, results)
    print(report)
    return report
