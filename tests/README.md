# Tests and manual checks

## Automated unit tests

The default pytest configuration discovers the automated suite in `tests/unit/`:

```bash
.venv/bin/pytest
```

Shared fixtures live in `tests/conftest.py`.

## Manual and diagnostic scripts

`tests/manual/` contains older, interactive, visual, or database-backed checks that are intentionally excluded from the default pytest run. From the repository root, run script-style checks as modules, for example:

```bash
.venv/bin/python -m tests.manual.test_comment_system
.venv/bin/python -m tests.manual.test_pwa
.venv/bin/python -m tests.manual.quick_check
.venv/bin/python -m tests.manual.check_urls
```

The Django `TestCase` script can be run explicitly with:

```bash
.venv/bin/pytest tests/manual/test_stock_distribution.py
```

Some manual scripts create or modify database records. Use them only with a development/test database, never a production database. The `visual_test.html` and `mamo.html` files are browser-based visual checks.
