# Provides encoding functionality to convert Python identifiers to Morse code
# representation using 'd' for dots, 'D' for dashes, and '_' as separators.
# Handles case sensitivity, underscore conventions, and collision detection.

import keyword


class MorseEncoder:
    """Encodes Python identifiers to a Morse code representation.

    Converts identifiers using 'd' for dots, 'D' for dashes, and '_' to
    separate Morse characters. Internal underscores are encoded as '__'.
    Leading and trailing underscores are preserved for Python conventions.
    """

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

    def __init__(self) -> None:
        """Initialize the encoder with an empty mapping cache."""
        self._name_mapping: dict[str, str] = {}
        self._encoded_to_originals: dict[str, list[str]] = {}

    def encode(self, name: str) -> str:
        """Encode a Python identifier to Morse representation.

        Args:
            name: The original identifier name.

        Returns:
            The Morse-encoded identifier, with collision disambiguation if needed.
        """
        if name in self._name_mapping:
            return self._name_mapping[name]

        encoded = self._encode_name(name)
        final_encoded = self._handle_collision(encoded, name)
        final_encoded = self._ensure_valid_identifier(final_encoded)

        self._name_mapping[name] = final_encoded

        base_key = self._get_base_encoded(encoded)
        if base_key not in self._encoded_to_originals:
            self._encoded_to_originals[base_key] = []
        self._encoded_to_originals[base_key].append(name)

        return final_encoded

    def _encode_name(self, name: str) -> str:
        """Encode a name to Morse without collision handling.

        Args:
            name: The identifier to encode.

        Returns:
            The raw Morse-encoded string.
        """
        leading_underscores = self._extract_leading_underscores(name)
        trailing_underscores = self._extract_trailing_underscores(name)

        core = name[len(leading_underscores) :]
        if trailing_underscores:
            core = core[: -len(trailing_underscores)]

        if not core:
            return name

        encoded_core = self._encode_core(core)
        return leading_underscores + encoded_core + trailing_underscores

    def _extract_leading_underscores(self, name: str) -> str:
        """Extract leading underscores from a name.

        Args:
            name: The identifier name.

        Returns:
            String containing all leading underscores.
        """
        count = 0
        for char in name:
            if char == "_":
                count += 1
            else:
                break
        return "_" * count

    def _extract_trailing_underscores(self, name: str) -> str:
        """Extract trailing underscores from a name.

        Args:
            name: The identifier name.

        Returns:
            String containing all trailing underscores.
        """
        count = 0
        for char in reversed(name):
            if char == "_":
                count += 1
            else:
                break
        return "_" * count

    def _encode_core(self, core: str) -> str:
        """Encode the core part of an identifier (without leading/trailing underscores).

        Args:
            core: The core identifier string.

        Returns:
            The Morse-encoded core string.
        """
        morse_parts: list[str] = []
        for char in core.lower():
            if char == "_":
                morse_parts.append("__")
            elif char in self.MORSE_TABLE:
                morse_code = self.MORSE_TABLE[char]
                encoded_char = morse_code.replace(".", "d").replace("-", "D")
                morse_parts.append(encoded_char)
            else:
                morse_parts.append(char)
        return "_".join(morse_parts)

    def _handle_collision(self, encoded: str, original: str) -> str:
        """Handle naming collisions by appending a numeric suffix.

        Args:
            encoded: The encoded name.
            original: The original identifier name.

        Returns:
            The encoded name with disambiguation suffix if needed.
        """
        base_key = self._get_base_encoded(encoded)

        if base_key not in self._encoded_to_originals:
            return encoded

        existing_originals = self._encoded_to_originals[base_key]
        if original in existing_originals:
            return self._name_mapping[original]

        suffix_num = len(existing_originals) + 1
        return f"{encoded}_{suffix_num}"

    def _get_base_encoded(self, encoded: str) -> str:
        """Get the base encoded name without collision suffix.

        Args:
            encoded: The encoded name possibly with suffix.

        Returns:
            The base encoded name.
        """
        return encoded.rstrip("_0123456789").rstrip("_")

    def _ensure_valid_identifier(self, name: str) -> str:
        """Ensure the encoded name is a valid Python identifier.

        Args:
            name: The encoded identifier name.

        Returns:
            A valid Python identifier, prefixed with 'm_' if necessary.
        """
        if keyword.iskeyword(name):
            return f"m_{name}"

        if name in dir(__builtins__):
            return f"m_{name}"

        if name and name[0].isdigit():
            return f"m_{name}"

        if not name.isidentifier():
            return f"m_{name}"

        return name

    def get_mapping(self) -> dict[str, str]:
        """Return a copy of the complete mapping of original to encoded names.

        Returns:
            Dictionary mapping original names to their encoded equivalents.
        """
        return self._name_mapping.copy()
