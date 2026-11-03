"""
tcgen.__main__
==============
CLI entry point.  Two subcommands:

  build-prompt <module.py>
      Concatenates the three prompt layers and the module source into
      prompt_out.md in the current working directory.

  check <module.py> <test_file.py> [--timeout N]
      Runs the verification pipeline (baseline pytest + mutation testing).
      (Pipeline implemented in runner.py / reporter.py — Step 3B.)
"""
import argparse
import sys
from pathlib import Path


def _cmd_build_prompt(args: argparse.Namespace) -> int:
    """Handler for the build-prompt subcommand."""
    from tcgen.prompt_builder import build_prompt

    module_path = Path(args.module)
    if not module_path.exists():
        print(f"error: module file not found: {module_path}", file=sys.stderr)
        return 1
    if not module_path.is_file():
        print(f"error: not a file: {module_path}", file=sys.stderr)
        return 1

    out_path = Path.cwd() / "prompt_out.md"
    try:
        build_prompt(module_path, out_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except SyntaxError as exc:
        print(f"error: syntax error in module: {exc}", file=sys.stderr)
        return 1

    print(f"prompt written -> {out_path}")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    """Handler for the check subcommand (pipeline not yet implemented)."""
    module_path = Path(args.module)
    test_path = Path(args.test_file)

    if not module_path.exists():
        print(f"error: module file not found: {module_path}", file=sys.stderr)
        return 1
    if not module_path.is_file():
        print(f"error: not a file: {module_path}", file=sys.stderr)
        return 1
    if not test_path.exists():
        print(f"error: test file not found: {test_path}", file=sys.stderr)
        return 1
    if not test_path.is_file():
        print(f"error: not a file: {test_path}", file=sys.stderr)
        return 1

    # Pipeline (runner + reporter) will be wired here in Step 3B.
    print("error: check pipeline not yet implemented", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="tcgen",
        description="Verified Test Case Generator — build prompts and verify tests.",
    )
    sub = parser.add_subparsers(dest="subcommand", metavar="<subcommand>")
    sub.required = True

    # --- build-prompt -------------------------------------------------------
    bp = sub.add_parser(
        "build-prompt",
        help="Assemble the LLM prompt from the three layers + module source.",
    )
    bp.add_argument("module", metavar="<module.py>", help="Python module to test.")
    bp.set_defaults(func=_cmd_build_prompt)

    # --- check --------------------------------------------------------------
    chk = sub.add_parser(
        "check",
        help="Run the verification pipeline (baseline + mutation testing).",
    )
    chk.add_argument("module", metavar="<module.py>", help="Python module to test.")
    chk.add_argument("test_file", metavar="<test_file.py>", help="pytest test file.")
    chk.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        metavar="N",
        help="Per-run pytest timeout in seconds (default: 10).",
    )
    chk.set_defaults(func=_cmd_check)

    return parser


def main() -> None:
    """Parse arguments and dispatch to the appropriate subcommand handler."""
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))
