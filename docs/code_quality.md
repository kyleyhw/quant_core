# Code Quality Workflow

This project enforces strict code quality standards using a modern toolchain. We use:

- **[Ruff](https://docs.astral.sh/ruff/)**: An extremely fast Python linter and formatter.
- **[Ty](https://github.com/astral-sh/ty)**: A zero-config static type checker (wrapper around MyPy/Pyright concepts) by Astral.
- **[Pre-commit](https://pre-commit.com/)**: A framework to manage and maintain multi-language pre-commit hooks.

## Quick Start

The workflow is automated via `pre-commit` hooks, which run on every `git commit`.

### Prerequisites

You need `uv` installed, as we use it to manage dependencies and run tools.

```bash
uv tool install pre-commit
```

### Installation

Install the pre-commit hooks into your git repository:

```bash
uv run pre-commit install
```

## Running Checks Manually

You can trigger the checks manually at any time using `uv` or `uvx`:

### 1. Linting & Auto-fixing
Identify and automatically fix linting errors (e.g., unused imports, style violations).

```bash
uv run ruff check --fix .
```

### 2. Formatting
Format code to adhere to the PEP 8 standard (and project-specific rules).

```bash
uv run ruff format .
```

### 3. Type Checking
Run strict static type analysis.

```bash
uvx ty check
```

## Configuration

- **Ruff**: Configured in `pyproject.toml` under the `[tool.ruff]` section.
- **Pre-commit**: Configured in `.pre-commit-config.yaml`.
- **Ty**: Zero-config by design, but adheres to standard type hinting practices.

## Troubleshooting

### "Ty not found"
If `uv run ty` fails, use `uvx ty check` as `ty` is often installed as a standalone tool.

### Pre-commit failures
If a hook fails (e.g., Ruff fixes a file), the commit will be aborted. Simply stage the modified files (`git add .`) and commit again.
