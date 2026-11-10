# Ruff setup and usage

Ruff is a Python linter and formatter, 10-100x faster than traditional tools. This project uses it to keep the code consistent and catch errors.

## Installation

Ruff is already in `requirements-api.txt`. Install with:

```bash
pip install -r requirements-api.txt
```

Or install it on its own:

```bash
pip install ruff>=0.3.0
```

## Basic commands

### Check for linting issues

```bash
ruff check .
```

Checks the whole project for style, import and logic errors, using the rules in `pyproject.toml`.

### Format code

```bash
ruff format .
```

Fixes formatting (whitespace, line length, imports). It is non-destructive and idempotent: a second run changes nothing.

### Check one file

```bash
ruff check motoquant/analysis/roi.py
```

### Auto-fix issues

```bash
ruff check --fix .
```

Corrects the violations Ruff can fix itself (imports, unused variables, upgrades to modern Python syntax).

## Configuration

Rules are defined in `pyproject.toml` under `[tool.ruff.lint]`:

| Code | Source | What it checks |
|---|---|---|
| E, W | PEP 8 style | line length, whitespace, etc. |
| F | Pyflakes | undefined names, unused imports, etc. |
| I | isort | import sorting and organization |
| UP | pyupgrade | modernize Python idioms |
| C4 | flake8-comprehensions | comprehension style |
| PIE | flake8-pie | miscellaneous improvements |

Two rules are ignored, because `ruff format` handles both: E501 (line too long) and W291 (trailing whitespace).

## Pre-commit hook (optional)

Add this to `.git/hooks/pre-commit` to run Ruff before commits:

```bash
#!/bin/sh
ruff check . || exit 1
ruff format --check . || exit 1
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

## Suggested workflow

1. Initial cleanup, once:
   ```bash
   ruff format .
   ruff check --fix .
   ```

2. During development:
   - Run `ruff check .` before committing to catch issues early.
   - Run `ruff format .` to fix most style issues automatically.

3. In CI/CD (future):
   ```bash
   ruff check . --exit-zero  # Report but don't fail
   ruff format --check .      # Fail if not formatted
   ```

## Notes

- Ruff needs no configuration by default; the rules above are sensible defaults for scientific Python code.
- The `[tool.pytest.ini_options]` section in `pyproject.toml` also documents the pytest configuration.
- `__init__.py` files ignore `F401` (unused imports) to allow public API exports like `from .roi import compute_parts_roi`.
- The cache is stored in `.ruff_cache/`. It is safe to delete; Ruff regenerates it.

## Troubleshooting

### "ruff not found"

Install it: `pip install ruff>=0.3.0`.

### Excluding a rule for one file

Add the rule to `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`.

### Ignoring a violation on one line

Add a comment: `x = 5  # noqa: F841` (ignores the unused variable).

### Performance

Ruff typically takes <100ms on this codebase, and the cache in `.ruff_cache/` speeds up repeat runs.
