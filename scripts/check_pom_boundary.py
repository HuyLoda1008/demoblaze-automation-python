"""Enforces the Page Object Model boundary in test files: tests must not
drive the DOM directly via page.<action>() -- use a page object method
instead. page.goto() is exempted (navigation is fine directly in tests).

This is a lightweight custom AST-based check, not an off-the-shelf linter
rule -- Python's lint ecosystem (ruff) has no equivalent to ESLint's
AST-selector no-restricted-syntax rules pluggable this cheaply. It mirrors
the TypeScript sibling project's eslint.config.js rule using the SAME
name-based heuristic (matches on a bare identifier named `page`, not
type-aware), for parity in spirit and behavior.
"""

import ast
import sys
from pathlib import Path

BANNED_METHODS = {
    'click',
    'fill',
    'check',
    'uncheck',
    'select_option',
    'hover',
    'dblclick',
    'tap',
    'type',
}


def check_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    violations = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in BANNED_METHODS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == 'page'
        ):
            violations.append(
                f'{path}:{node.lineno}: page.{node.func.attr}() called directly -- '
                f'add or use a page object method instead (see CODE_CONVENTIONS.md '
                f'"Page Object Model"). page.goto() for navigation is fine.'
            )
    return violations


def main() -> int:
    all_violations = [v for f in sorted(Path('tests').rglob('test_*.py')) for v in check_file(f)]
    for violation in all_violations:
        print(violation)
    return 1 if all_violations else 0


if __name__ == '__main__':
    sys.exit(main())
