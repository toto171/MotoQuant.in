# Ruff Setup & Usage Guide

Ruff is an extremely fast Python linter and formatter (10-100x faster than traditional tools). This project uses Ruff to enforce code quality and consistency.

## Installation

Ruff is already in `requirements-api.txt`. Install with:

```bash
pip install -r requirements-api.txt
```

Or install individually:

```bash
pip install ruff>=0.3.0
```

## Basic Commands

### Check for linting issues

```bash
ruff check .
```

Checks the entire project for style/import/logic errors based on the rules in `pyproject.toml`.

### Auto-format code

```bash
ruff format .
```

Automatically fixes formatting issues (whitespace, line length, imports). This is non-destructive and idempotent.

### Check specific file

```bash
ruff check motoquant/analysis/roi.py
```

### Auto-fix specific issues

```bash
ruff check --fix .
```

Automatically corrects fixable linting violations (imports, unused variables, upgrades to modern Python syntax).

## Configuration

Rules are defined in `pyproject.toml` under `[tool.ruff.lint]`:

- **E, W**: PEP 8 style (line length, whitespace, etc.)
- **F**: Pyflakes (undefined names, unused imports, etc.)
- **I**: isort (import sorting and organization)
- **UP**: pyupgrade (modernize Python idioms)
- **C4**: flake8-comprehensions (improve comprehension style)
- **PIE**: flake8-pie (miscellaneous improvements)

Ignored rules:
- **E501**: Line too long (ruff format handles this automatically)
- **W291**: Trailing whitespace (ruff format handles this)

## Pre-commit Hook (Optional)

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

## Workflow Recommendations

1. **Initial cleanup** (one-time):
   ```bash
   ruff format .
   ruff check --fix .
   ```

2. **During development**:
   - Run `ruff check .` before committing to catch issues early
   - Use `ruff format .` to fix most style issues automatically

3. **In CI/CD** (future):
   ```bash
   ruff check . --exit-zero  # Report but don't fail
   ruff format --check .      # Fail if not formatted
   ```

## Notes

- Ruff is **zero-config** by default; these rules are sensible defaults for scientific Python code
- The `[tool.pytest.ini_options]` section in `pyproject.toml` also documents pytest configuration
- `__init__.py` files ignore `F401` (unused imports) to allow public API exports like `from .roi import compute_parts_roi`
- Cache is stored in `.ruff_cache/` — safe to delete, will be regenerated

## Troubleshooting

**"ruff not found"**
- Ensure you've installed: `pip install ruff>=0.3.0`

**Want to exclude a specific rule for a file?**
- Add to `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`

**Want to ignore a violation in a single line?**
- Add comment: `x = 5  # noqa: F841` (ignore unused variable)

**Performance?**
- Ruff is extremely fast (typically <100ms on this codebase)
- Cache in `.ruff_cache/` speeds up repeat runs
