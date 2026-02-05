# Transforms Python source code by renaming identifiers to Morse encoding while
# preserving formatting, comments, and string literals. Uses AST for identifier
# collection and tokenization for precise source-level replacement.

from __future__ import annotations

import ast
import keyword
import re
import tokenize
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from morse_encoder import MorseEncoder


class CodeTransformer:
    """Transforms Python source code with Morse-encoded identifiers.

    Collects identifiers to rename via AST analysis, then performs token-based
    transformation to preserve original formatting, comments, and strings.
    """

    BUILTINS: frozenset[str] = frozenset(dir(__builtins__))
    PROTECTED_IMPORTS: frozenset[str] = frozenset({
        "Path",
        "Any",
        "Optional",
        "Union",
        "List",
        "Dict",
        "Set",
        "Tuple",
        "Callable",
        "Iterator",
        "Iterable",
        "Generator",
        "Sequence",
        "Mapping",
        "Type",
        "TypeVar",
        "Generic",
        "Protocol",
        "Final",
        "Literal",
        "ClassVar",
        "Self",
    })
    PROTECTED_NAMES: frozenset[str] = frozenset({"self", "cls"})

    def __init__(self, encoder: MorseEncoder) -> None:
        """Initialize the transformer with the given encoder.

        Args:
            encoder: The MorseEncoder instance to use for name encoding.
        """
        self._encoder = encoder
        self._names_to_rename: set[str] = set()
        self._import_bindings: set[str] = set()
        self._import_lines: dict[int, ast.Import | ast.ImportFrom] = {}
        self._method_names: set[str] = set()
        self._class_attributes: set[str] = set()

    def transform(self, source: str) -> str:
        """Transform the source code by renaming identifiers to Morse encoding.

        Args:
            source: The original Python source code.

        Returns:
            The transformed source code with Morse-encoded identifiers.

        Raises:
            SyntaxError: If the source code cannot be parsed.
        """
        tree = ast.parse(source)

        self._collect_names(tree)

        has_annotations = self._check_for_annotations(tree)
        has_future_import = self._check_for_future_annotations(tree)

        transformed = self._transform_tokens(source)
        transformed = self._transform_fstrings(transformed)
        transformed = self._transform_imports(transformed)

        if has_annotations and not has_future_import:
            transformed = self._prepend_future_import(transformed, source)

        return transformed

    def _collect_names(self, tree: ast.Module) -> None:
        """Collect all identifier names that should be renamed.

        Args:
            tree: The parsed AST of the source code.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._collect_class_attributes(node)

        for node in ast.walk(tree):
            self._collect_from_node(node)

    def _collect_class_attributes(self, node: ast.ClassDef) -> None:
        """Collect class attribute names to exclude from renaming.

        Args:
            node: A class definition node.
        """
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                self._class_attributes.add(item.target.id)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self._class_attributes.add(target.id)

    def _collect_from_node(self, node: ast.AST) -> None:
        """Collect renamable identifiers from a single AST node.

        Args:
            node: An AST node to examine.
        """
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            self._collect_from_function(node)
        elif isinstance(node, ast.ClassDef):
            self._collect_from_class(node)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            self._maybe_add_name(node.id)
        elif isinstance(node, ast.Import):
            self._collect_from_import(node)
        elif isinstance(node, ast.ImportFrom):
            self._collect_from_import_from(node)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            self._maybe_add_name(node.name)
        elif isinstance(node, ast.Global | ast.Nonlocal):
            for name in node.names:
                self._maybe_add_name(name)
        elif isinstance(node, ast.NamedExpr):
            self._maybe_add_name(node.target.id)

    def _collect_from_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Collect renamable identifiers from a function definition.

        Args:
            node: A function or async function definition node.
        """
        if not self._is_dunder(node.name) and not self._is_protected(node.name):
            self._names_to_rename.add(node.name)
            self._method_names.add(node.name)

        all_args = (
            node.args.args
            + node.args.posonlyargs
            + node.args.kwonlyargs
        )
        for arg in all_args:
            self._maybe_add_name(arg.arg)

        if node.args.vararg:
            self._maybe_add_name(node.args.vararg.arg)
        if node.args.kwarg:
            self._maybe_add_name(node.args.kwarg.arg)

    def _collect_from_class(self, node: ast.ClassDef) -> None:
        """Collect the class name if it should be renamed.

        Args:
            node: A class definition node.
        """
        self._maybe_add_name(node.name)

    def _collect_from_import(self, node: ast.Import) -> None:
        """Collect renamable identifiers from an import statement.

        Args:
            node: An import statement node.
        """
        self._import_lines[node.lineno] = node
        for alias in node.names:
            if alias.asname:
                # Explicit alias: rename the alias
                binding_name = alias.asname
                if not self._is_protected(binding_name):
                    self._import_bindings.add(binding_name)
                    self._names_to_rename.add(binding_name)
            elif "." not in alias.name:
                # Simple import (no dots): rename the module name
                binding_name = alias.name
                if not self._is_protected(binding_name):
                    self._import_bindings.add(binding_name)
                    self._names_to_rename.add(binding_name)
            # Dotted imports without alias (e.g., `import a.b.c`) are left unchanged
            # because the binding `a` is used as `a.b.c.method()` via attribute access

    def _collect_from_import_from(self, node: ast.ImportFrom) -> None:
        """Collect renamable identifiers from a from-import statement.

        Args:
            node: A from-import statement node.
        """
        if node.module == "__future__":
            return
        self._import_lines[node.lineno] = node
        for alias in node.names:
            if alias.name == "*":
                continue
            binding_name = alias.asname if alias.asname else alias.name
            if not self._is_protected(binding_name):
                self._import_bindings.add(binding_name)
                self._names_to_rename.add(binding_name)

    def _maybe_add_name(self, name: str) -> None:
        """Add a name to the rename set if it passes all checks.

        Args:
            name: The identifier name to potentially add.
        """
        if self._is_dunder(name):
            return
        if self._is_protected(name):
            return
        if name in self._class_attributes:
            return
        self._names_to_rename.add(name)

    def _is_dunder(self, name: str) -> bool:
        """Check if name is a dunder (double underscore) name.

        Args:
            name: The identifier name to check.

        Returns:
            True if the name is a dunder name.
        """
        return name.startswith("__") and name.endswith("__")

    def _is_protected(self, name: str) -> bool:
        """Check if name should not be renamed.

        Args:
            name: The identifier name to check.

        Returns:
            True if the name is a keyword, builtin, or protected import.
        """
        if keyword.iskeyword(name):
            return True
        if name in self.BUILTINS:
            return True
        if name in self.PROTECTED_IMPORTS:
            return True
        if name in self.PROTECTED_NAMES:
            return True
        return False

    def _check_for_annotations(self, tree: ast.Module) -> bool:
        """Check if the code has any type annotations.

        Args:
            tree: The parsed AST of the source code.

        Returns:
            True if the code contains type annotations.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if node.returns:
                    return True
                all_args = (
                    node.args.args
                    + node.args.posonlyargs
                    + node.args.kwonlyargs
                )
                for arg in all_args:
                    if arg.annotation:
                        return True
                if node.args.vararg and node.args.vararg.annotation:
                    return True
                if node.args.kwarg and node.args.kwarg.annotation:
                    return True
            elif isinstance(node, ast.AnnAssign):
                return True
        return False

    def _check_for_future_annotations(self, tree: ast.Module) -> bool:
        """Check if the code already has from __future__ import annotations.

        Args:
            tree: The parsed AST of the source code.

        Returns:
            True if the future annotations import is present.
        """
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                if node.module == "__future__":
                    for alias in node.names:
                        if alias.name == "annotations":
                            return True
            elif not isinstance(node, ast.Expr):
                break
        return False

    def _transform_tokens(self, source: str) -> str:
        """Transform source by replacing NAME tokens with encoded versions.

        Args:
            source: The original source code.

        Returns:
            The transformed source code.

        Raises:
            SyntaxError: If tokenization fails.
        """
        try:
            tokens = list(
                tokenize.generate_tokens(StringIO(source).readline)
            )
        except tokenize.TokenizeError as err:
            raise SyntaxError(f"Failed to tokenize source: {err}") from err

        replacements = self._compute_replacements(tokens)
        return self._apply_replacements(source, replacements)

    def _compute_replacements(
        self, tokens: list[tokenize.TokenInfo]
    ) -> list[tuple[int, int, int, int, str]]:
        """Compute all token replacements needed.

        Args:
            tokens: List of tokens from the source.

        Returns:
            List of (start_row, start_col, end_row, end_col, new_text) tuples.
        """
        replacements: list[tuple[int, int, int, int, str]] = []

        for i, tok in enumerate(tokens):
            if tok.type != tokenize.NAME:
                continue
            if tok.string not in self._names_to_rename:
                continue
            if tok.start[0] in self._import_lines:
                continue

            is_attr = self._is_attribute_access(tokens, i)
            is_method = tok.string in self._method_names

            if is_attr and not is_method:
                continue

            encoded = self._encoder.encode(tok.string)
            start_row, start_col = tok.start
            end_row, end_col = tok.end
            replacements.append((start_row, start_col, end_row, end_col, encoded))

        return replacements

    def _is_attribute_access(
        self, tokens: list[tokenize.TokenInfo], index: int
    ) -> bool:
        """Check if the token at index is an attribute access (after a dot).

        Args:
            tokens: List of all tokens.
            index: Index of the current token to check.

        Returns:
            True if the token follows a dot operator.
        """
        for j in range(index - 1, -1, -1):
            prev_tok = tokens[j]
            if prev_tok.type in (
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.COMMENT,
                tokenize.ENCODING,
            ):
                continue
            if prev_tok.type == tokenize.OP and prev_tok.string == ".":
                return True
            break
        return False

    def _apply_replacements(
        self,
        source: str,
        replacements: list[tuple[int, int, int, int, str]],
    ) -> str:
        """Apply replacements to source code from end to start.

        Args:
            source: The original source code.
            replacements: List of replacement tuples.

        Returns:
            The source code with all replacements applied.
        """
        lines = source.splitlines(keepends=True)

        if lines and not lines[-1].endswith(("\n", "\r")):
            lines[-1] += "\n"

        sorted_replacements = sorted(
            replacements, key=lambda r: (r[0], r[1]), reverse=True
        )

        for start_row, start_col, end_row, end_col, new_text in sorted_replacements:
            row_idx = start_row - 1
            if row_idx < len(lines):
                line = lines[row_idx]
                lines[row_idx] = line[:start_col] + new_text + line[end_col:]

        result = "".join(lines)
        if source and not source.endswith("\n"):
            result = result.rstrip("\n")

        return result

    def _prepend_future_import(self, source: str, original: str) -> str:
        """Prepend the future annotations import to the source.

        Args:
            source: The transformed source code.
            original: The original source code (to detect docstring).

        Returns:
            Source with future import prepended at the correct position.
        """
        future_import = "from __future__ import annotations\n"

        try:
            tree = ast.parse(original)
        except SyntaxError:
            return future_import + source

        insert_line = 0
        if tree.body and isinstance(tree.body[0], ast.Expr):
            first_node = tree.body[0]
            if isinstance(first_node.value, ast.Constant):
                if isinstance(first_node.value.value, str):
                    insert_line = first_node.end_lineno or 0

        lines = source.splitlines(keepends=True)
        if insert_line == 0:
            return future_import + source
        else:
            return (
                "".join(lines[:insert_line])
                + future_import
                + "".join(lines[insert_line:])
            )

    def _transform_imports(self, source: str) -> str:
        """Transform import statements to use 'as' clauses with encoded names.

        Args:
            source: The source code with non-import names already transformed.

        Returns:
            Source code with import statements properly transformed.
        """
        if not self._import_lines:
            return source

        lines = source.splitlines(keepends=True)
        if lines and not lines[-1].endswith(("\n", "\r")):
            lines[-1] += "\n"

        for lineno, node in sorted(self._import_lines.items(), reverse=True):
            line_idx = lineno - 1
            if line_idx >= len(lines):
                continue

            new_line = self._reconstruct_import(node)
            original_line = lines[line_idx]
            trailing_comment = self._extract_trailing_comment(original_line)
            indentation = self._extract_indentation(original_line)

            lines[line_idx] = indentation + new_line + trailing_comment + "\n"

        result = "".join(lines)
        if source and not source.endswith("\n"):
            result = result.rstrip("\n")

        return result

    def _reconstruct_import(self, node: ast.Import | ast.ImportFrom) -> str:
        """Reconstruct an import statement with encoded aliases.

        Args:
            node: The import AST node.

        Returns:
            The reconstructed import statement string.
        """
        if isinstance(node, ast.Import):
            return self._reconstruct_simple_import(node)
        else:
            return self._reconstruct_from_import(node)

    def _reconstruct_simple_import(self, node: ast.Import) -> str:
        """Reconstruct a simple 'import x' statement.

        Args:
            node: The Import AST node.

        Returns:
            The reconstructed import statement.
        """
        parts: list[str] = []
        for alias in node.names:
            module_name = alias.name

            if alias.asname:
                # Explicit alias provided
                original_binding = alias.asname
                if self._is_protected(original_binding):
                    parts.append(f"{module_name} as {alias.asname}")
                else:
                    encoded = self._encoder.encode(original_binding)
                    parts.append(f"{module_name} as {encoded}")
            elif "." in module_name:
                # Dotted import without alias: leave unchanged
                parts.append(module_name)
            else:
                # Simple import without alias
                if self._is_protected(module_name):
                    parts.append(module_name)
                else:
                    encoded = self._encoder.encode(module_name)
                    parts.append(f"{module_name} as {encoded}")

        return "import " + ", ".join(parts)

    def _reconstruct_from_import(self, node: ast.ImportFrom) -> str:
        """Reconstruct a 'from x import y' statement.

        Args:
            node: The ImportFrom AST node.

        Returns:
            The reconstructed import statement.
        """
        module = node.module or ""
        level_dots = "." * node.level

        parts: list[str] = []
        for alias in node.names:
            import_name = alias.name

            if import_name == "*":
                parts.append("*")
                continue

            if alias.asname:
                original_binding = alias.asname
            else:
                original_binding = import_name

            if self._is_protected(original_binding):
                if alias.asname:
                    parts.append(f"{import_name} as {alias.asname}")
                else:
                    parts.append(import_name)
            else:
                encoded = self._encoder.encode(original_binding)
                parts.append(f"{import_name} as {encoded}")

        return f"from {level_dots}{module} import " + ", ".join(parts)

    def _extract_trailing_comment(self, line: str) -> str:
        """Extract any trailing comment from a line.

        Args:
            line: The source line.

        Returns:
            The trailing comment including '#', or empty string.
        """
        in_string = False
        string_char = None

        for i, char in enumerate(line):
            if char in ('"', "'") and (i == 0 or line[i - 1] != "\\"):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            elif char == "#" and not in_string:
                return "  " + line[i:].rstrip("\n\r")

        return ""

    def _extract_indentation(self, line: str) -> str:
        """Extract leading whitespace from a line.

        Args:
            line: The source line.

        Returns:
            The leading whitespace.
        """
        stripped = line.lstrip()
        return line[: len(line) - len(stripped)]

    def _transform_fstrings(self, source: str) -> str:
        """Transform variable names inside f-string expressions.

        This method provides compatibility for Python < 3.12 where f-strings
        are tokenized as single STRING tokens rather than being broken down
        into FSTRING_START/FSTRING_MIDDLE/FSTRING_END tokens.

        Args:
            source: The source code with other transformations already applied.

        Returns:
            Source code with f-string expressions also transformed.
        """
        # Pattern to match f-strings (f"...", f'...', F"...", F'...')
        # Also handles raw f-strings (rf"...", fr"...", etc.)
        fstring_pattern = re.compile(
            r'([fF][rRbBuU]?|[rRbBuU]?[fF])'
            r'(["\'])\2\2(.+?)\2\2\2'  # Triple-quoted
            r'|'
            r'([fF][rRbBuU]?|[rRbBuU]?[fF])'
            r'(["\'])(.+?)\5',  # Single-quoted (non-greedy)
            re.DOTALL
        )

        result = []
        last_end = 0

        for match in fstring_pattern.finditer(source):
            result.append(source[last_end:match.start()])

            if match.group(3) is not None:
                prefix = match.group(1)
                quote = match.group(2) * 3
                content = match.group(3)
            else:
                prefix = match.group(4)
                quote = match.group(5)
                content = match.group(6)

            transformed_content = self._transform_fstring_content(content)
            result.append(f"{prefix}{quote}{transformed_content}{quote}")
            last_end = match.end()

        result.append(source[last_end:])
        return "".join(result)

    def _transform_fstring_content(self, content: str) -> str:
        """Transform variable names within f-string content.

        Args:
            content: The content inside an f-string (between quotes).

        Returns:
            Content with variable names transformed.
        """
        result = []
        i = 0

        while i < len(content):
            if content[i] == "{":
                if i + 1 < len(content) and content[i + 1] == "{":
                    result.append("{{")
                    i += 2
                    continue

                brace_start = i
                expr_end = self._find_matching_brace(content, i)
                if expr_end == -1:
                    result.append(content[i])
                    i += 1
                    continue

                expr = content[brace_start + 1 : expr_end]
                transformed_expr = self._transform_fstring_expr(expr)
                result.append("{" + transformed_expr + "}")
                i = expr_end + 1
            elif content[i] == "}" and i + 1 < len(content) and content[i + 1] == "}":
                result.append("}}")
                i += 2
            else:
                result.append(content[i])
                i += 1

        return "".join(result)

    def _find_matching_brace(self, content: str, start: int) -> int:
        """Find the matching closing brace for an f-string expression.

        Args:
            content: The f-string content.
            start: Index of the opening brace.

        Returns:
            Index of the matching closing brace, or -1 if not found.
        """
        depth = 0
        in_string = False
        string_char = None
        i = start

        while i < len(content):
            char = content[i]

            if in_string:
                if char == "\\" and i + 1 < len(content):
                    i += 2
                    continue
                if char == string_char:
                    in_string = False
                i += 1
                continue

            if char in ('"', "'"):
                if i + 2 < len(content) and content[i : i + 3] == char * 3:
                    in_string = True
                    string_char = char * 3
                    i += 3
                    continue
                in_string = True
                string_char = char
                i += 1
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return i

            i += 1

        return -1

    def _transform_fstring_expr(self, expr: str) -> str:
        """Transform a single f-string expression.

        Args:
            expr: The expression inside braces (without the braces).

        Returns:
            The transformed expression.
        """
        # Split off format spec and conversion (e.g., "x!r:.2f" -> "x", "!r", ":.2f")
        # Handle nested braces in format specs
        main_expr = expr
        suffix = ""

        # Find conversion flag (!s, !r, !a)
        conv_match = re.search(r"![sra]", expr)
        # Find format spec (starts with :)
        colon_pos = self._find_format_colon(expr)

        if conv_match and (colon_pos == -1 or conv_match.start() < colon_pos):
            if colon_pos != -1:
                main_expr = expr[: conv_match.start()]
                suffix = expr[conv_match.start() :]
            else:
                main_expr = expr[: conv_match.start()]
                suffix = expr[conv_match.start() :]
        elif colon_pos != -1:
            main_expr = expr[:colon_pos]
            suffix = expr[colon_pos:]

        transformed_main = self._transform_expression_names(main_expr)
        return transformed_main + suffix

    def _find_format_colon(self, expr: str) -> int:
        """Find the colon that starts a format spec (not inside brackets/parens).

        Args:
            expr: The f-string expression.

        Returns:
            Index of format spec colon, or -1 if not found.
        """
        depth = 0
        in_string = False
        string_char = None

        for i, char in enumerate(expr):
            if in_string:
                if char == "\\" and i + 1 < len(expr):
                    continue
                if char == string_char:
                    in_string = False
                continue

            if char in ('"', "'"):
                in_string = True
                string_char = char
                continue

            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == ":" and depth == 0:
                return i

        return -1

    def _transform_expression_names(self, expr: str) -> str:
        """Transform variable names in an expression string.

        Args:
            expr: A Python expression string.

        Returns:
            The expression with variable names transformed.
        """
        # Pattern to match identifiers
        # Match word boundaries but not after a dot (attribute access)
        identifier_pattern = re.compile(r"(?<![.\w])([A-Za-z_][A-Za-z0-9_]*)(?![.\w])")

        def replace_name(match: re.Match[str]) -> str:
            name = match.group(1)
            if name in self._names_to_rename:
                return self._encoder.encode(name)
            return name

        return identifier_pattern.sub(replace_name, expr)
