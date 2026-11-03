"""
tcgen.__main__
==============
CLI entry point.  Two subcommands:

  build-prompt <module.py>
      Concatenates the three prompt layers and the module source into
      prompt_out.md in the current working directory.

  check <module.py> <test_file.py> [--timeout N]
      Runs the verification pipeline (baseline pytest + mutation testing).
      (Pipeline implemented in runner.py / reporter.py -- Step 3B.)
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
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"prompt written -> {out_path}")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    """Handler for the check subcommand -- full verification pipeline."""
    import ast as _ast

    from tcgen.mutator import generate_mutants
    from tcgen.reporter import MutantResult, print_report
    from tcgen.runner import Classification, run_in_sandbox

    module_path = Path(args.module).resolve()
    test_path = Path(args.test_file).resolve()
    timeout: float = args.timeout

    # --- Input validation ---------------------------------------------------
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

    # --- Load and validate source syntax ------------------------------------
    try:
        source = module_path.read_text(encoding="utf-8")
        _ast.parse(source)
    except SyntaxError as exc:
        print(f"error: syntax error in {module_path.name}: {exc}", file=sys.stderr)
        return 1

    module_dir = module_path.parent
    module_filename = module_path.name

    # --- Baseline gate ------------------------------------------------------
    print("Running baseline (original source) ...")
    baseline = run_in_sandbox(
        module_source=source,
        module_filename=module_filename,
        module_dir=module_dir,
        test_path=test_path,
        timeout=timeout,
    )
    if baseline.exit_code != 0 or baseline.collected == 0:
        if baseline.exit_code == -1:
            print("error: baseline timed out -- tests took too long on the original code.",
                  file=sys.stderr)
        elif baseline.collected == 0:
            print("error: pytest collected 0 tests. "
                  "Check that the test file is not empty and imports are correct.",
                  file=sys.stderr)
        else:
            print("error: tests FAIL on the original code. "
                  "Fix the tests (or the code) before running mutation testing.",
                  file=sys.stderr)
        print("\n--- pytest output ---", file=sys.stderr)
        print(baseline.raw_output, file=sys.stderr)
        return 1

    # --- Control run (unparse round-trip) -----------------------------------
    try:
        unparsed_source = _ast.unparse(_ast.parse(source))
    except Exception as exc:
        print(f"error: ast.unparse failed: {exc}", file=sys.stderr)
        return 1

    print("Running control (ast.unparse round-trip) ...")
    control = run_in_sandbox(
        module_source=unparsed_source,
        module_filename=module_filename,
        module_dir=module_dir,
        test_path=test_path,
        timeout=timeout,
    )
    if control.exit_code != 0:
        print("error: tests FAIL against ast.unparse(source). "
              "The unparse round-trip changed observable behaviour. "
              "Check for f-strings, complex decorators, or encoding-sensitive code.",
              file=sys.stderr)
        print("\n--- pytest output ---", file=sys.stderr)
        print(control.raw_output, file=sys.stderr)
        return 1

    # --- Mutation testing ---------------------------------------------------
    mutants = generate_mutants(source)

    if not mutants:
        print("\nno mutation sites found -- nothing to mutate.")
        # Still show baseline info without a score.
        from tcgen.reporter import build_report
        from tcgen.runner import RunResult
        print_report(baseline, control, [])
        return 0

    print(f"Generated {len(mutants)} mutant(s). Running ...\n")

    results: list[MutantResult] = []
    for i, mutant in enumerate(mutants, 1):
        desc = mutant.site.description.encode("ascii", "replace").decode("ascii")
        print(f"  [{i}/{len(mutants)}] {desc}", end=" ... ", flush=True)
        run = run_in_sandbox(
            module_source=mutant.mutated_source,
            module_filename=module_filename,
            module_dir=module_dir,
            test_path=test_path,
            timeout=timeout,
        )
        # Override classification to TIMEOUT when the subprocess timed out.
        if run.exit_code == -1:
            run.classification = Classification.TIMEOUT
        print(run.classification.value)
        results.append(MutantResult(mutant=mutant, classification=run.classification))

    print()
    print_report(baseline, control, results)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="tcgen",
        description="Verified Test Case Generator -- build prompts and verify tests.",
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


if __name__ == "__main__":
    main()
