# morsify: The Variable Renamer Nobody Asked For

![Code Base: AI Vibes](https://img.shields.io/badge/Code%20Base-AI%20Vibes%20%F0%9F%A4%A0-blue)

> *"Because `x` was just too readable"* - Ancient Proverb

## What Is This Madness?

Ever looked at your beautifully crafted Python code and thought, "You know what this needs? More dots and dashes"? No? Well, we did it anyway.

**morsify** transforms your pristine, readable Python identifiers into glorious Morse code representations. Your coworkers will love you. Your code reviewers will definitely not block your PRs. Your future self will thank you when debugging at 3 AM.

### Before

```python
def calculate_sum(num1, num2):
    result = num1 + num2
    return result
```

### After

```python
def DdDd_dD_dDdd_DdDd_ddD_dDdd_dD_D_d____ddd_ddD_DD(Dd_ddD_DD_dDDDD, Dd_ddD_DD_ddDDD):
    dDd_d_ddd_ddD_dDdd_D = Dd_ddD_DD_dDDDD + Dd_ddD_DD_ddDDD
    return dDd_d_ddd_ddD_dDdd_D
```

*Chef's kiss*

## The "Encoding"

We use a sophisticated, military-grade encoding scheme:

| Symbol | Meaning |
|--------|---------|
| `d` | dot (.) |
| `D` | dash (-) |
| `_` | separator between letters |
| `__` | an actual underscore in the original name |

So `hello` becomes `dddd_d_dDdd_dDdd_DDD` because:
- h = `....` = `dddd`
- e = `.` = `d`
- l = `.-..` = `dDdd`
- l = `.-..` = `dDdd`
- o = `---` = `DDD`

It's like Morse code, but worse!

## Features

- Transforms function names, class names, and variables
- Preserves Python keywords (we're chaotic, not monsters)
- Keeps `self` and `cls` intact (some traditions are sacred)
- Handles f-strings correctly (we have standards)
- Leaves attribute access alone (`obj.attr` stays readable-ish)
- Maintains leading/trailing underscores (`_private` stays `_<morse>`)
- Collision detection (because `ad` and `da` would be too easy)

## Installation

```bash
git clone https://github.com/yourusername/morsify.git
cd morsify
# That's it. No dependencies. We're not animals.
```

## Usage

### Transform a Python File

```bash
python morsify.py your_script.py
# Creates morse--your_script.py in the same directory
```

### Preview an Identifier

Want to know what your variable will become? Use the preview tool:

```bash
python str2morse.py my_variable
# Output: DD_DdDD____dddD_dD_dDd_dd_dD_Dddd_dDdd_d
```

### Example: str2morse.py

<details>
<summary>Show example input and output</summary>

Here's a simple utility that converts strings to our Morse encoding:

```python
import argparse


MORSE_TABLE: dict[str, str] = {
    "a": ".-",  "b": "-...",  "c": "-.-.",  "d": "-..",
    "e": ".",   "f": "..-.",  "g": "--.",   "h": "....",
    "i": "..",  "j": ".---",  "k": "-.-",   "l": ".-..",
    "m": "--",  "n": "-.",    "o": "---",   "p": ".--.",
    "q": "--.-", "r": ".-.",  "s": "...",   "t": "-",
    "u": "..-", "v": "...-",  "w": ".--",   "x": "-..-",
    "y": "-.--", "z": "--..", "0": "-----", "1": ".----",
    "2": "..---", "3": "...--", "4": "....-", "5": ".....",
    "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}


def encode_string(text: str) -> str:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert string to Morse encoding")
    parser.add_argument("text", help="String to convert")
    args = parser.parse_args()
    print(encode_string(args.text))


if __name__ == "__main__":
    main()
```

And here's what it looks like after running it through morsify:

```python
from __future__ import annotations

import argparse as dD_dDd_DDd_dDDd_dD_dDd_ddd_d


DD_DDD_dDd_ddd_d____D_dD_Dddd_dDdd_d: dict[str, str] = {
    "a": ".-",  "b": "-...",  "c": "-.-.",  "d": "-..",
    "e": ".",   "f": "..-.",  "g": "--.",   "h": "....",
    "i": "..",  "j": ".---",  "k": "-.-",   "l": ".-..",
    "m": "--",  "n": "-.",    "o": "---",   "p": ".--.",
    "q": "--.-", "r": ".-.",  "s": "...",   "t": "-",
    "u": "..-", "v": "...-",  "w": ".--",   "x": "-..-",
    "y": "-.--", "z": "--..", "0": "-----", "1": ".----",
    "2": "..---", "3": "...--", "4": "....-", "5": ".....",
    "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}


def d_Dd_DdDd_DDD_Ddd_d____ddd_D_dDd_dd_Dd_DDd(D_d_DddD_D: str) -> str:
    DD_DDD_dDd_ddd_d____dDDd_dD_dDd_D_ddd: list[str] = []
    for DdDd_dddd_dD_dDd in D_d_DddD_D.lower():
        if DdDd_dddd_dD_dDd == "_":
            DD_DDD_dDd_ddd_d____dDDd_dD_dDd_D_ddd.append("__")
        elif DdDd_dddd_dD_dDd in DD_DDD_dDd_ddd_d____D_dD_Dddd_dDdd_d:
            DD_DDD_dDd_ddd_d____DdDd_DDD_Ddd_d = DD_DDD_dDd_ddd_d____D_dD_Dddd_dDdd_d[DdDd_dddd_dD_dDd]
            d_Dd_DdDd_DDD_Ddd_d_Ddd____DdDd_dddd_dD_dDd = DD_DDD_dDd_ddd_d____DdDd_DDD_Ddd_d.replace(".", "d").replace("-", "D")
            DD_DDD_dDd_ddd_d____dDDd_dD_dDd_D_ddd.append(d_Dd_DdDd_DDD_Ddd_d_Ddd____DdDd_dddd_dD_dDd)
        else:
            DD_DDD_dDd_ddd_d____dDDd_dD_dDd_D_ddd.append(DdDd_dddd_dD_dDd)
    return "_".join(DD_DDD_dDd_ddd_d____dDDd_dD_dDd_D_ddd)


def DD_dD_dd_Dd() -> None:
    dD_dDd_DDd_ddd = dDDd_dD_dDd_ddd_d____dD_dDd_DDd_ddD_DD_d_Dd_D_ddd()
    d_Dd_DdDd_DDD_Ddd_d_Ddd = d_Dd_DdDd_DDD_Ddd_d____ddd_D_dDd_dd_Dd_DDd(dD_dDd_DDd_ddd.text)
    print(d_Dd_DdDd_DDD_Ddd_d_Ddd)


if __name__ == "__main__":
    DD_dD_dd_Dd()
```

*Gorgeous. Maintainable. A true masterpiece of software engineering.*

For the curious, here's what happened to some key identifiers:

| Original | Morse-ified |
|----------|-------------|
| `MORSE_TABLE` | `DD_DDD_dDd_ddd_d____D_dD_Dddd_dDdd_d` |
| `encode_string` | `d_Dd_DdDd_DDD_Ddd_d____ddd_D_dDd_dd_Dd_DDd` |
| `morse_parts` | `DD_DDD_dDd_ddd_d____dDDd_dD_dDd_D_ddd` |
| `char` | `DdDd_dddd_dD_dDd` |
| `main` | `DD_dD_dd_Dd` |
| `text` | `D_d_DddD_D` |

Both versions produce identical output. One is just... *better*.

</details>

## Legitimate Use Cases

1. **Code Obfuscation** - Make your code unreadable to protect your intellectual property (and your own sanity)
2. **Team Building** - Nothing brings developers together like shared suffering
3. **Job Security** - Good luck replacing the one person who can read this
4. **Interview Prep** - *"Tell me about a time you overcame a technical challenge"*
5. **Art** - It's a statement about the human condition, probably?

## What We Don't Touch

- Python keywords (`if`, `for`, `while`, etc.)
- Built-in functions (`print`, `len`, `range`, etc.)
- Dunder methods (`__init__`, `__str__`, etc.)
- String contents and comments (we're not *that* evil)
- Type annotations from `typing` module

## FAQ

**Q: Why?**
A: Why not?

**Q: Is this production-ready?**
A: Define *"production."*

**Q: Can I reverse the transformation?**
A: Technically yes. Emotionally? The scars remain.

**Q: My code review was rejected. What do I do?**
A: Find a new team that appreciates art.

**Q: Does this work with Python 2?**
A: It's 2026. Let it go!

## Requirements

- Python 3.12+ *(we use the fancy new f-string tokenization)*
- A sense of humor
- Plausible deniability

## Contributing

Found a bug? Want to add a feature? Consider this: what if you didn't?

Just kidding. PRs welcome. Please include tests and a valid excuse.

## License

MIT License - Do whatever you want. We're not responsible for any code reviews, HR meetings, or existential crises that may result from using this tool.

## Acknowledgments

- [My Inspiration](https://www.reddit.com/r/ProgrammerHumor/comments/1qvxfvb/confidentialinformation/)
- Samuel Morse, for the original idea
- Whoever decided variable names should be *"descriptive"*
- Coffee

---

*Remember: With great power comes great responsibility. Use morsify wisely.*

*Or don't. We're a README, not a cop.*
