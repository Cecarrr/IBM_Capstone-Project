"""
tcgen.prompt_builder
====================
Assembles the LLM prompt from three Markdown layer files and a Python module.

Output file layout
------------------
  [Layer 1 - Role & Context]
  ---
  [Layer 2 - Testing Task]
  ---
  [Layer 3 - Output Format]
  ---
  [MODULE SOURCE: <filename>]
  ```python          (fence length >= longest backtick run in source + 1)
  <source>
  ```
"""
import ast
from pathlib import Path

# Prompt layer filenames in concatenation order.
_LAYER_FILES = ("layer1_role.md", "layer2_task.md", "layer3_output.md")

# The prompts/ directory sits next to the tcgen/ package, i.e. two levels up from
# this file (tcgen/prompt_builder.py → tcgen/ → project root).
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_layer(name: str) -> str:
    """Read and return the content of a single prompt layer file.

    Raises FileNotFoundError with a user-friendly message when the file is absent.
    """
    path = _PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"prompt layer file not found: {path}\n"
            f"Expected all three layers under {_PROMPTS_DIR}"
        )
    return path.read_text(encoding="utf-8")


def _validate_syntax(source: str, module_path: Path) -> None:
    """Parse the module source and raise SyntaxError if it is invalid."""
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise SyntaxError(
            f"syntax error in {module_path}: {exc.msg} (line {exc.lineno})"
        ) from exc


def build_prompt(module_path: Path, out_path: Path) -> None:
    """Concatenate the three prompt layers and the module source into *out_path*.

    Parameters
    ----------
    module_path:
        Path to the Python module whose tests we want to generate.
    out_path:
        Destination file (prompt_out.md).  Created or overwritten.

    Raises
    ------
    FileNotFoundError
        If any prompt layer file is missing.
    SyntaxError
        If the module source cannot be parsed.
    """
    source = module_path.read_text(encoding="utf-8")
    _validate_syntax(source, module_path)

    sections: list[str] = []

    for layer_name in _LAYER_FILES:
        sections.append(_load_layer(layer_name))

    # Choose a code fence longer than any run of backticks inside the source,
    # so that source files containing ``` cannot break the Markdown fence.
    import re as _re
    max_backticks = max(
        (len(m.group()) for m in _re.finditer(r"`+", source)),
        default=2,
    )
    fence = "`" * max(3, max_backticks + 1)

    # Append the module source as a fenced code block.
    sections.append(
        f"## MODULE SOURCE: {module_path.name}\n\n"
        f"{fence}python\n{source}\n{fence}"
    )

    separator = "\n\n---\n\n"
    prompt_text = separator.join(sections) + "\n"

    out_path.write_text(prompt_text, encoding="utf-8")
