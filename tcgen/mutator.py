"""
tcgen.mutator
=============
AST-based mutation testing engine.

Design
------
Two-pass approach (per approved plan revision E):

  Pass 1 — enumerate_sites(source)
      Walk the AST once, depth-first left-to-right.  Record every mutable node as a
      MutationSite with a stable index.

  Pass 2 — apply_mutation(source, site)
      Re-parse a fresh tree.  Walk again in the same order; when the counter reaches
      the site's index, transform exactly that node.  Return ast.unparse(new_tree).

  generate_mutants(source) -> list[Mutant]
      Call both passes for each site and return the complete list.

Mutation operators
------------------
  arithmetic  : BinOp Add  <-> Sub,  Mult <-> Div
  comparison  : Lt <-> LtE,  Gt <-> GtE,  Eq <-> NotEq
  boolean     : BoolOp And <-> Or
  constant    : numeric literal n  ->  n + 1
                (bool constants skipped; non-numeric constants skipped)
  return value: return <non-None expr>  ->  return None
                (return None -> return None is skipped)

Determinism guarantee
---------------------
The AST walk is depth-first with children visited in their natural list order
(ast.walk visits breadth-first, so we use a recursive visitor instead).
"""
import ast
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MutationSite:
    """A single mutable location identified during the enumeration pass."""
    index: int           # stable 0-based position in the depth-first walk
    lineno: int          # line number in the original source (1-based)
    col_offset: int      # column in the original source
    description: str     # human-readable "original → mutant" label


@dataclass(frozen=True)
class Mutant:
    """A mutation site together with the resulting mutated source string."""
    site: MutationSite
    mutated_source: str


# ---------------------------------------------------------------------------
# Operator tables
# ---------------------------------------------------------------------------

# Arithmetic: each entry is (original_op_type, replacement_op_type, label)
_ARITHMETIC_OPS: list[tuple[type, type, str]] = [
    (ast.Add,  ast.Sub,  "+ → -"),
    (ast.Sub,  ast.Add,  "- → +"),
    (ast.Mult, ast.Div,  "* → /"),
    (ast.Div,  ast.Mult, "/ → *"),
]

# Comparison: cmpop nodes inside ast.Compare
_COMPARISON_OPS: list[tuple[type, type, str]] = [
    (ast.Lt,    ast.LtE,   "< → <="),
    (ast.LtE,   ast.Lt,    "<= → <"),
    (ast.Gt,    ast.GtE,   "> → >="),
    (ast.GtE,   ast.Gt,    ">= → >"),
    (ast.Eq,    ast.NotEq, "== → !="),
    (ast.NotEq, ast.Eq,    "!= → =="),
]

# Boolean: boolop nodes inside ast.BoolOp
_BOOLEAN_OPS: list[tuple[type, type, str]] = [
    (ast.And, ast.Or,  "and → or"),
    (ast.Or,  ast.And, "or → and"),
]


# ---------------------------------------------------------------------------
# Visitor helpers
# ---------------------------------------------------------------------------

def _iter_child_nodes_ordered(node: ast.AST):
    """Yield child nodes in the order they appear in the source (field order)."""
    for _field, value in ast.iter_fields(node):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, ast.AST):
                    yield item
        elif isinstance(value, ast.AST):
            yield value


def _walk_depth_first(node: ast.AST):
    """Depth-first, left-to-right generator over all nodes in the AST."""
    yield node
    for child in _iter_child_nodes_ordered(node):
        yield from _walk_depth_first(child)


# ---------------------------------------------------------------------------
# Site enumeration helpers
# ---------------------------------------------------------------------------

def _lineno(node: ast.AST) -> int:
    return getattr(node, "lineno", 0)


def _col(node: ast.AST) -> int:
    return getattr(node, "col_offset", 0)


def _collect_sites_from_node(
    node: ast.AST,
    counter: list[int],   # mutable single-element list used as a shared counter
    sites: list[MutationSite],
) -> None:
    """
    Examine *node* and append any MutationSite entries it generates.
    Updates counter[0] for each site produced.
    """
    # --- Arithmetic (BinOp) -------------------------------------------------
    if isinstance(node, ast.BinOp):
        for orig_type, _repl_type, label in _ARITHMETIC_OPS:
            if isinstance(node.op, orig_type):
                sites.append(MutationSite(
                    index=counter[0],
                    lineno=_lineno(node),
                    col_offset=_col(node),
                    description=f"arithmetic {label} (line {_lineno(node)})",
                ))
                counter[0] += 1
                break  # only one arithmetic op per BinOp node

    # --- Comparison (Compare) -----------------------------------------------
    elif isinstance(node, ast.Compare):
        for i, op in enumerate(node.ops):
            for orig_type, _repl_type, label in _COMPARISON_OPS:
                if isinstance(op, orig_type):
                    sites.append(MutationSite(
                        index=counter[0],
                        lineno=_lineno(node),
                        col_offset=_col(node),
                        description=(
                            f"comparison op[{i}] {label} (line {_lineno(node)})"
                        ),
                    ))
                    counter[0] += 1
                    break

    # --- Boolean (BoolOp) ---------------------------------------------------
    elif isinstance(node, ast.BoolOp):
        for orig_type, _repl_type, label in _BOOLEAN_OPS:
            if isinstance(node.op, orig_type):
                sites.append(MutationSite(
                    index=counter[0],
                    lineno=_lineno(node),
                    col_offset=_col(node),
                    description=f"boolean {label} (line {_lineno(node)})",
                ))
                counter[0] += 1
                break

    # --- Constant (numeric only, not bool) ----------------------------------
    elif isinstance(node, ast.Constant):
        val = node.value
        # Skip bool constants (bool is a subclass of int in Python)
        if isinstance(val, bool):
            return
        if isinstance(val, (int, float)):
            sites.append(MutationSite(
                index=counter[0],
                lineno=_lineno(node),
                col_offset=_col(node),
                description=f"constant {val!r} → {val + 1!r} (line {_lineno(node)})",
            ))
            counter[0] += 1

    # --- Return value -------------------------------------------------------
    elif isinstance(node, ast.Return):
        # Skip `return None` (explicit or implicit)
        if node.value is None:
            return
        if isinstance(node.value, ast.Constant) and node.value.value is None:
            return
        sites.append(MutationSite(
            index=counter[0],
            lineno=_lineno(node),
            col_offset=_col(node),
            description=f"return value → None (line {_lineno(node)})",
        ))
        counter[0] += 1


def enumerate_sites(source: str) -> list[MutationSite]:
    """Walk the AST of *source* and return all mutable sites in deterministic order.

    Parameters
    ----------
    source:
        Valid Python source code as a string.

    Returns
    -------
    list[MutationSite]
        Sites indexed 0, 1, 2, … in depth-first, left-to-right AST order.
    """
    tree = ast.parse(source)
    counter: list[int] = [0]
    sites: list[MutationSite] = []
    for node in _walk_depth_first(tree):
        _collect_sites_from_node(node, counter, sites)
    return sites


# ---------------------------------------------------------------------------
# Mutation application
# ---------------------------------------------------------------------------

class _MutationTransformer(ast.NodeTransformer):
    """Apply exactly one mutation (identified by *target_index*) to the tree.

    The transformer walks the tree in the same depth-first order as
    enumerate_sites, increments an internal counter, and transforms only the
    node whose position matches *target_index*.
    """

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.applied = False  # set to True once the mutation is made

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_mutate(self) -> bool:
        """Return True if the current counter matches the target site."""
        hit = self._counter == self._target
        self._counter += 1
        return hit

    # ------------------------------------------------------------------
    # Key ordering invariant
    # ------------------------------------------------------------------
    # enumerate_sites visits each node BEFORE its children (pre-order),
    # records a site, then the loop continues into children.
    #
    # NodeTransformer calls visit_X, which we are responsible for.
    # We must consume the counter slot for THIS node first, then call
    # generic_visit to descend into children — regardless of whether we
    # mutate or not.
    #
    # visit_Return special case: when we replace the return value we must
    # still call generic_visit on the original node so that child nodes
    # (e.g. the BinOp subtree) have their counter slots consumed.
    # We call generic_visit BEFORE replacing node.value so it walks the
    # original children; the mutations those children produce are
    # discarded (we overwrite node.value afterwards).
    # ------------------------------------------------------------------

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        # 1. Check this node's slot.
        mutate_here = False
        replacement_op = None
        for orig_type, repl_type, _label in _ARITHMETIC_OPS:
            if isinstance(node.op, orig_type):
                if self._should_mutate():
                    mutate_here = True
                    replacement_op = repl_type()
                break

        # 2. Descend into children regardless.
        self.generic_visit(node)

        if mutate_here:
            node.op = replacement_op
            self.applied = True
        return node

    def visit_Compare(self, node: ast.Compare) -> Any:
        # 1. Check each comparator's slot.
        replacements: dict[int, Any] = {}
        for i, op in enumerate(node.ops):
            for orig_type, repl_type, _label in _COMPARISON_OPS:
                if isinstance(op, orig_type):
                    if self._should_mutate():
                        replacements[i] = repl_type()
                    break

        # 2. Descend into children regardless.
        self.generic_visit(node)

        if replacements:
            for i, new_op in replacements.items():
                node.ops[i] = new_op
            self.applied = True
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        # 1. Check this node's slot.
        mutate_here = False
        replacement_op = None
        for orig_type, repl_type, _label in _BOOLEAN_OPS:
            if isinstance(node.op, orig_type):
                if self._should_mutate():
                    mutate_here = True
                    replacement_op = repl_type()
                break

        # 2. Descend into children regardless.
        self.generic_visit(node)

        if mutate_here:
            node.op = replacement_op
            self.applied = True
        return node

    def visit_Constant(self, node: ast.Constant) -> Any:
        val = node.value
        if isinstance(val, bool):
            return node  # do not count, do not mutate (no children to visit)
        if isinstance(val, (int, float)):
            if self._should_mutate():
                node.value = val + 1
                self.applied = True
        return node

    def visit_Return(self, node: ast.Return) -> Any:
        is_return_none = (
            node.value is None
            or (isinstance(node.value, ast.Constant) and node.value.value is None)
        )

        if not is_return_none:
            # 1. Check this node's slot BEFORE descending.
            mutate_here = self._should_mutate()
            # 2. Descend into original children so their counter slots are consumed.
            self.generic_visit(node)
            if mutate_here:
                node.value = ast.Constant(value=None)
                ast.fix_missing_locations(node)
                self.applied = True
            return node

        # return None — no slot to consume, just descend.
        self.generic_visit(node)
        return node


def _walk_order_matches_enumerate(transformer: _MutationTransformer) -> None:
    """
    The NodeTransformer visits children via generic_visit, which iterates
    fields in declaration order — the same order used by _walk_depth_first.
    This comment documents the invariant; no code needed.
    """


def apply_mutation(source: str, site: MutationSite) -> str:
    """Re-parse *source* and apply the mutation described by *site*.

    Returns the unparsed mutated source as a string.

    Parameters
    ----------
    source:
        Original Python source.
    site:
        A MutationSite previously returned by enumerate_sites(source).

    Raises
    ------
    RuntimeError
        If the transformer did not find the target site (should never happen
        when source and site are derived from the same original source).
    """
    tree = ast.parse(source)
    transformer = _MutationTransformer(target_index=site.index)
    new_tree = transformer.visit(tree)
    if not transformer.applied:
        raise RuntimeError(
            f"Mutation site {site.index} was not found during application pass. "
            "This is a bug in the mutator — please report it."
        )
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree)


def generate_mutants(source: str) -> list[Mutant]:
    """Return all mutants for *source* in deterministic order.

    For each MutationSite produced by enumerate_sites, re-parses the source
    and applies exactly that one mutation.

    Parameters
    ----------
    source:
        Valid Python source code.

    Returns
    -------
    list[Mutant]
        One Mutant per site, in the same order as enumerate_sites.
    """
    sites = enumerate_sites(source)
    return [Mutant(site=s, mutated_source=apply_mutation(source, s)) for s in sites]
