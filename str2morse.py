# Converts a string to the "special" Morse code encoding format used by the
# Morse identifier transformer. Useful for previewing how identifiers will
# be encoded or for generating test cases.

import argparse


MORSE_TABLE: dict[str, str] = {
    "a": ".-",
    "b": "-...",
    "c": "-.-.",
    "d": "-..",
    "e": ".",
    "f": "..-.",
    "g": "--.",
    "h": "....",
    "i": "..",
    "j": ".---",
    "k": "-.-",
    "l": ".-..",
    "m": "--",
    "n": "-.",
    "o": "---",
    "p": ".--.",
    "q": "--.-",
    "r": ".-.",
    "s": "...",
    "t": "-",
    "u": "..-",
    "v": "...-",
    "w": ".--",
    "x": "-..-",
    "y": "-.--",
    "z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
}


def encode_string(text: str) -> str:
    """Encode a string to Morse code format.

    Args:
        text: The input string to encode.

    Returns:
        The Morse-encoded string using 'd' for dots, 'D' for dashes,
        '_' between characters, and '__' for underscores.
    """
    morse_parts: list[str] = []

    for char in text.lower():
        if char == "_":
            morse_parts.append("__")
        elif char in MORSE_TABLE:
            morse_code = MORSE_TABLE[char]
            encoded_char = morse_code.replace(".", "d").replace("-", "D")
            morse_parts.append(encoded_char)
        else:
            morse_parts.append(char)

    return "_".join(morse_parts)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Namespace containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert a string to Morse code encoding format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python str2morse.py hello        # Output: dddd_d_dDdd_dDdd_DDD
  python str2morse.py my_var       # Output: DD_DdDD___dddD_dD_dDd
  python str2morse.py VERSION      # Output: dddD_d_dDd_ddd_dd_DDD_Dd
        """,
    )
    parser.add_argument(
        "text",
        type=str,
        help="The string to convert to Morse encoding",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    encoded = encode_string(args.text)
    print(encoded)


if __name__ == "__main__":
    main()
