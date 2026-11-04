"""
tests/test_examples.py
======================
Integration tests asserting the health of examples/ and examples/buggy/.

Tests use real pytest subprocesses (via run_in_sandbox) and real file I/O.
"""
import difflib
import doctest
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT      = Path(__file__).parent.parent
EXAMPLES  = ROOT / "examples"
BUGGY     = EXAMPLES / "buggy"
SAMPLETST = EXAMPLES / "sample_tests"

sys.path.insert(0, str(ROOT))

from tcgen.runner import Classification, run_in_sandbox


# ---------------------------------------------------------------------------
# C5-a: doctests of all three example modules pass
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module_name", [
    "grade_calculator",
    "password_checker",
    "date_overlap",
])
def test_doctests_pass(module_name: str):
    """Run the module's own doctests via importlib so functions are in scope."""
    import importlib.util
    module_file = EXAMPLES / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, str(module_file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = doctest.testmod(mod, verbose=False, optionflags=doctest.ELLIPSIS)
    assert result.failed == 0, \
        f"{module_name}: {result.failed}/{result.attempted} doctest(s) failed"


# ---------------------------------------------------------------------------
# C5-b: each buggy file differs by exactly one line from examples/
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module_name", [
    "grade_calculator",
    "password_checker",
    "date_overlap",
])
def test_buggy_differs_by_one_line(module_name: str):
    orig  = (EXAMPLES / f"{module_name}.py").read_text(encoding="utf-8").splitlines()
    buggy = (BUGGY   / f"{module_name}.py").read_text(encoding="utf-8").splitlines()
    assert len(orig) == len(buggy), \
        f"{module_name}: line count differs ({len(orig)} vs {len(buggy)})"
    changed = sum(1 for a, b in zip(orig, buggy) if a != b)
    assert changed == 1, \
        f"{module_name}: expected 1 changed line, got {changed}"


# ---------------------------------------------------------------------------
# C5-c: BUGS.md mentions all three module names
# ---------------------------------------------------------------------------

def test_bugs_md_mentions_all_modules():
    content = (BUGGY / "BUGS.md").read_text(encoding="utf-8").lower()
    for name in ("grade_calculator", "password_checker", "date_overlap"):
        assert name in content, f"BUGS.md does not mention {name}"


# ---------------------------------------------------------------------------
# C5-d: strong reference tests PASS on examples/grade_calculator.py
#        and FAIL on examples/buggy/grade_calculator.py
# ---------------------------------------------------------------------------

def test_strong_tests_pass_on_good_module():
    good_src = (EXAMPLES / "grade_calculator.py").read_text(encoding="utf-8")
    test_path = SAMPLETST / "test_grade_calculator_strong.py"
    result = run_in_sandbox(
        module_source=good_src,
        module_filename="grade_calculator.py",
        module_dir=EXAMPLES,
        test_path=test_path,
        timeout=30.0,
    )
    assert result.classification == Classification.SURVIVED, \
        f"Strong tests should pass on good module.\nOutput:\n{result.raw_output}"


def test_strong_tests_fail_on_buggy_module():
    buggy_src = (BUGGY / "grade_calculator.py").read_text(encoding="utf-8")
    test_path = SAMPLETST / "test_grade_calculator_strong.py"
    result = run_in_sandbox(
        module_source=buggy_src,
        module_filename="grade_calculator.py",
        module_dir=BUGGY,
        test_path=test_path,
        timeout=30.0,
    )
    assert result.classification == Classification.KILLED, \
        f"Strong tests should fail on buggy module.\nOutput:\n{result.raw_output}"


# ---------------------------------------------------------------------------
# C5-e: `check` score: strong suite >= 100%, weak suite < 50%
#        (using run_in_sandbox directly for speed)
# ---------------------------------------------------------------------------

def _mutation_score(module_path: Path, test_path: Path) -> float:
    """Run the full check pipeline and return the mutation score (0.0-1.0)."""
    import ast as _ast
    from tcgen.mutator import generate_mutants
    from tcgen.reporter import MutantResult
    from tcgen.runner import Classification, run_in_sandbox

    source = module_path.read_text(encoding="utf-8")
    module_dir = module_path.parent

    mutants = generate_mutants(source)
    if not mutants:
        return 1.0

    killed = survived = timeouts = 0
    for m in mutants:
        r = run_in_sandbox(
            module_source=m.mutated_source,
            module_filename=module_path.name,
            module_dir=module_dir,
            test_path=test_path,
            timeout=10.0,
        )
        if r.classification in (Classification.KILLED,):
            killed += 1
        elif r.classification == Classification.TIMEOUT:
            timeouts += 1
        elif r.classification == Classification.SURVIVED:
            survived += 1
    denom = killed + timeouts + survived
    return (killed + timeouts) / denom if denom else 0.0


def test_strong_suite_scores_100_percent():
    score = _mutation_score(
        EXAMPLES / "grade_calculator.py",
        SAMPLETST / "test_grade_calculator_strong.py",
    )
    assert score == 1.0, f"Strong suite score {score:.1%} < 100%"


def test_weak_suite_scores_below_50_percent():
    score = _mutation_score(
        EXAMPLES / "grade_calculator.py",
        SAMPLETST / "test_grade_calculator_weak.py",
    )
    assert score < 0.50, f"Weak suite score {score:.1%} should be below 50%"


# ---------------------------------------------------------------------------
# C5-f: password_checker probes
# ---------------------------------------------------------------------------

def _load_check_strength():
    """Load check_strength from examples/password_checker.py via importlib."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "password_checker_examples", str(EXAMPLES / "password_checker.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check_strength


def test_space_is_not_a_symbol():
    check_strength = _load_check_strength()
    # 12-char, has upper+lower+digit, but only spaces as "symbol" -> medium
    # "Abcdef gh12 " has a space; space is not in string.punctuation
    pw = "Abcdef gh12 "
    assert len(pw) == 12
    assert check_strength(pw) == "medium", \
        "Space should not count as a symbol"


def test_e_acute_is_not_lowercase():
    check_strength = _load_check_strength()
    # 12 chars: A,B,C,D,E + e-acute (not ASCII lower) + 1,2,3,4,5 + !
    pw = "ABCDE\xe912345!"
    assert len(pw) == 12, f"Expected 12 chars, got {len(pw)}: {pw!r}"
    result = check_strength(pw)
    # No ASCII lowercase letter -> not strong
    assert result != "strong", \
        "e-acute should not count as a lowercase ASCII letter"


def test_11_char_password_never_strong():
    check_strength = _load_check_strength()
    pw = "Abcdefg1!23"   # 11 chars, all classes present
    assert len(pw) == 11
    assert check_strength(pw) == "medium"


def test_12_char_all_classes_is_strong():
    check_strength = _load_check_strength()
    pw = "Abcdefgh123!"   # 12 chars, a-z, A-Z, 0-9, punctuation
    assert len(pw) == 12
    assert check_strength(pw) == "strong"
