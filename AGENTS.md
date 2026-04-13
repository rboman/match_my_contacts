# Repository Guidelines

## Project Structure & Module Organization
Core Python code lives in `src/running_contacts/`. The current CLI entry point is `src/running_contacts/cli.py`, exposed as the `running-contacts` console script via `pyproject.toml`. Keep new modules inside `src/running_contacts/` and group them by responsibility as the project grows. Use `tests/` for automated tests and `data/` for local input or exported files that should not become application logic.

## Build, Test, and Development Commands
Create a virtual environment and install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the CLI locally with `running-contacts hello` to confirm the entry point works. Use `pytest -q` to run tests. At the moment the suite is empty, so contributors adding behavior should add tests alongside the change.

## Coding Style & Naming Conventions
Target Python 3.11+ and prefer the standard library where practical. Follow PEP 8: 4-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and short, explicit docstrings where they add value. Keep CLI commands small and move reusable logic into separate modules instead of growing `cli.py` into a catch-all file. Typing is encouraged for public functions and any matching or parsing logic.

## Testing Guidelines
Use `pytest` for all automated tests. Mirror the package structure under `tests/`; for example, logic added in `src/running_contacts/matching.py` should usually get coverage in `tests/test_matching.py`. Prefer focused unit tests over broad integration tests, especially for parsing, normalization, and name-matching behavior. Add regression tests for bug fixes.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit subjects such as `Add gitignore and initial project skeleton`. Keep that pattern: one-line summary, imperative mood, and specific scope. Pull requests should explain the functional change, note any new commands or data expectations, and link related issues or notes when relevant. Include CLI examples when behavior visible to users changes.

## Data & Configuration Notes
Treat `data/` as local workspace data. Do not commit private contact exports, credentials, or generated datasets unless they are sanitized and intentionally added as fixtures.
