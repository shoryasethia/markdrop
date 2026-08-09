# Contributing to Markdrop

## Development setup

```bash
git clone https://github.com/shoryasethia/markdrop.git
cd markdrop
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality checks

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

## Pull request checklist

1. Add or update tests for behavior changes.
2. Update `CHANGELOG.md` under an unreleased or versioned heading.
3. Keep README/docs aligned with CLI output and Python API behavior.
4. Ensure CI passes locally before opening a PR.

## License

Contributions are made under the GPL-3.0 license.
