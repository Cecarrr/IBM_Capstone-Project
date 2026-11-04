"""
tests/test_mutator.py
=====================
Unit tests for tcgen.mutator.

Every test is deterministic and uses only the source code passed directly
as a string -- no file I/O.
"""
import ast
import difflib
import sys
from pathlib import Path

import pytest

# Make sure the project root is importable when running from any directory.
sys.path.insert(0, str(Path(__file__).parent.parent))

from tcgen.mutator import (
    Mutant,
    MutationSite,
    _MutationTransformer,
    apply_mutation,
    enumerate_sites,
    generate_mutants,
)

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_DEMO_SOURCE = """\
def f(a, b):
    if a >= b and b != 0:
        return a - b + 1
    return None
"""

# Rich fixture: one of every supported construct so we can assert the
# invariants (compile, one-line diff, ASCII description, non-empty source line).
_RICH_SOURCE = """\
import asyncio
import string

CONSTANT = 42

class Greeter:
    def greet(self, name: str) -> str:
        return f"Hello {name}"

def add(x: int, y: int) -> int:
    \"\"\"Return x + y.\"\"\"
    if x > 0 and y >= 0:
        total = x + y
        total += 1
        return total
    return 0

def check(items: list) -> bool:
    return len(items) != 0

def nested():
    def inner(n: int) -> int:
        return n - 1
    return inner

def with_lambda():
    fn = lambda z: z + 1
    return fn(10)

def with_walrus(data: list) -> int:
    if (n := len(data)) > 0:
        return n
    return 0

def ternary(x: int) -> int:
    return x + 1 if x > 0 else x - 1

def with_loop(items: list) -> int:
    total = 0
    for item in items:
        total += item
    return total

def with_comprehension(items: list) -> list:
    return [x + 1 for x in items if x > 0]

async def async_fn(x: int) -> int:
    await asyncio.sleep(0)
    return x + 1
"""


def _compile_ok(source: str) -> bool:
    try:
        compile(source, "<mutant>", "exec")
        return True
    except SyntaxError:
        return False


def _differs_by_one_line(original: str, mutated: str) -> bool:
    """Return True if the two sources differ on exactly one line."""
    orig_lines = original.splitlines()
    mut_lines  = mutated.splitlines()
    if len(orig_lines) != len(mut_lines):
        return False
    diff_count = sum(1 for a, b in zip(orig_lines, mut_lines) if a != b)
    return diff_count == 1


# ---------------------------------------------------------------------------
# C1-a: demo source gives exactly 8 sites
# ---------------------------------------------------------------------------

def test_demo_source_gives_8_sites():
    sites = enumerate_sites(_DEMO_SOURCE)
    assert len(sites) == 8, f"Expected 8, got {len(sites)}: {[s.description for s in sites]}"


# ---------------------------------------------------------------------------
# C1-b: return None is never mutated
# ---------------------------------------------------------------------------

def test_return_none_not_mutated():
    source = "def f():\n    return None\n"
    mutants = generate_mutants(source)
    assert mutants == [], "return None should produce no mutants"


# ---------------------------------------------------------------------------
# C1-c: bool constants are never mutated
# ---------------------------------------------------------------------------

def test_bool_constants_not_mutated():
    source = "def f():\n    x = True\n    y = False\n    return x\n"
    mutants = generate_mutants(source)
    # The only mutable site is `return x -> return None`
    descs = [m.site.description for m in mutants]
    for d in descs:
        assert "True" not in d and "False" not in d, \
            f"Bool constant mutated: {d}"


# ---------------------------------------------------------------------------
# C1-d: AugAssign += -> -=
# ---------------------------------------------------------------------------

def test_augassign_plus_becomes_minus():
    source = "def f(x):\n    x += 1\n    return x\n"
    mutants = generate_mutants(source)
    aug_mutants = [m for m in mutants if "augassign" in m.site.description]
    assert len(aug_mutants) >= 1
    assert any("+= -> -=" in m.site.description for m in aug_mutants)


# ---------------------------------------------------------------------------
# C1-e: chained comparison (a < b < c produces two sites)
# ---------------------------------------------------------------------------

def test_chained_comparison_two_sites():
    source = "def f(a, b, c):\n    return a < b < c\n"
    sites = enumerate_sites(source)
    comp_sites = [s for s in sites if "comparison" in s.description]
    assert len(comp_sites) == 2, f"Expected 2 comparison sites, got {len(comp_sites)}"


# ---------------------------------------------------------------------------
# C1-f: negative constants are mutated (n -> n+1, so -1 -> 0)
# ---------------------------------------------------------------------------

def test_negative_constant_mutated():
    source = "def f():\n    return -1\n"
    # ast.parse gives: Return(value=UnaryOp(op=USub(), operand=Constant(value=1)))
    # The Constant(1) IS mutated to 2; the unary minus stays.
    mutants = generate_mutants(source)
    const_mutants = [m for m in mutants if "constant" in m.site.description]
    assert len(const_mutants) >= 1
    # Mutated source changes the 1 inside the unary minus
    assert any("1" in m.site.description for m in const_mutants)


# ---------------------------------------------------------------------------
# C1-g: no-site source gives []
# ---------------------------------------------------------------------------

def test_no_site_source():
    source = "def f():\n    pass\n"
    assert generate_mutants(source) == []


# ---------------------------------------------------------------------------
# C1-h: apply_mutation with out-of-range index raises RuntimeError
# ---------------------------------------------------------------------------

def test_apply_mutation_bad_site_raises():
    source = _DEMO_SOURCE
    sites = enumerate_sites(source)
    bad_site = MutationSite(
        index=999,
        lineno=1,
        col_offset=0,
        description="fake",
        _source_line="",
    )
    with pytest.raises(RuntimeError):
        apply_mutation(source, bad_site)


# ---------------------------------------------------------------------------
# C1-i: INVARIANT on rich fixture
# ---------------------------------------------------------------------------

def test_rich_fixture_invariants():
    source = _RICH_SOURCE
    orig_unparsed = ast.unparse(ast.parse(source))
    mutants = generate_mutants(source)

    assert len(mutants) > 0, "Rich fixture should have at least one mutant"

    # Run twice and compare -- determinism
    mutants2 = generate_mutants(source)
    assert [(m.site.index, m.site.description) for m in mutants] == \
           [(m.site.index, m.site.description) for m in mutants2], \
           "generate_mutants is not deterministic"

    for m in mutants:
        # 1. Compiles
        assert _compile_ok(m.mutated_source), \
            f"Mutant {m.site.index} does not compile: {m.site.description}"

        # 2. Differs from original by exactly one line
        assert _differs_by_one_line(orig_unparsed, m.mutated_source), \
            f"Mutant {m.site.index} differs by != 1 line: {m.site.description}"

        # 3. Description is pure ASCII
        assert m.site.description.isascii(), \
            f"Non-ASCII description: {m.site.description!r}"

        # 4. Source line is non-empty
        assert m.site._source_line.strip() != "", \
            f"Empty source line for site {m.site.index}: {m.site.description}"


# ---------------------------------------------------------------------------
# C1-j: counter invariant -- transformer visits the same number of slots
#         as enumerate_sites for every site in the demo source
# ---------------------------------------------------------------------------

def test_transformer_counter_invariant():
    source = _DEMO_SOURCE
    sites = enumerate_sites(source)
    n = len(sites)
    for s in sites:
        tree = ast.parse(source)
        t = _MutationTransformer(target_index=s.index)
        t.visit(tree)
        assert t.applied, f"Site {s.index} was not applied"
        assert t._counter == n, \
            f"Site {s.index}: counter ended at {t._counter}, expected {n}"
