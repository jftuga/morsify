# CLI entry point for the Morse code identifier transformer. Takes a Python
# source file as input and produces a transformed output file with all
# eligible identifiers renamed to their Morse code equivalents.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from code_transformer import CodeTransformer
from morse_encoder import MorseEncoder


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Namespace containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Transform Python identifiers to Morse code encoding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python main.py script.py\n"
            "  -> Creates morse--script.py in the same directory"
        ),
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the Python file to transform (must end in .py)",
    )
    return parser.parse_args()


def validate_input_file(file_path: Path) -> None:
    """Validate that the input file exists and has a .py extension.

    Args:
        file_path: Path to the input file.

    Raises:
        SystemExit: If validation fails.
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.is_file():
        print(f"Error: Not a file: {file_path}", file=sys.stderr)
        sys.exit(1)

    if file_path.suffix != ".py":
        print(f"Error: File must have .py extension: {file_path}", file=sys.stderr)
        sys.exit(1)


def read_source_file(file_path: Path) -> str:
    """Read the source code from a file.

    Args:
        file_path: Path to the source file.

    Returns:
        The file contents as a string.

    Raises:
        SystemExit: If the file cannot be read.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as err:
        print(f"Error: Could not read file: {err}", file=sys.stderr)
        sys.exit(1)


def transform_source(source: str) -> str:
    """Transform the source code using Morse encoding.

    Args:
        source: The original Python source code.

    Returns:
        The transformed source code.

    Raises:
        SystemExit: If transformation fails due to syntax errors.
    """
    encoder = MorseEncoder()
    transformer = CodeTransformer(encoder)

    try:
        return transformer.transform(source)
    except SyntaxError as err:
        print(f"Error: Invalid Python syntax: {err}", file=sys.stderr)
        sys.exit(1)


def compute_output_path(input_path: Path) -> Path:
    """Compute the output file path.

    Args:
        input_path: Path to the input file.

    Returns:
        Path where the output file should be saved.
    """
    output_name = f"morse--{input_path.name}"
    return input_path.parent / output_name


def write_output_file(file_path: Path, content: str) -> None:
    """Write the transformed content to a file.

    Args:
        file_path: Path where the file should be written.
        content: The content to write.

    Raises:
        SystemExit: If the file cannot be written.
    """
    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as err:
        print(f"Error: Could not write file: {err}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the Morse transformer CLI."""
    args = parse_arguments()
    input_path = Path(args.input_file)

    validate_input_file(input_path)

    source = read_source_file(input_path)
    transformed = transform_source(source)

    output_path = compute_output_path(input_path)
    write_output_file(output_path, transformed)

    print(f"Transformed: {input_path} -> {output_path}")


if __name__ == "__main__":
    main()
