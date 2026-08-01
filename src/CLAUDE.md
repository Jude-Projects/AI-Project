# src/ — conventions

Note: the root `CLAUDE.md` describes an unrelated project (Colaberry). It does not apply here. This file is the actual convention for this folder.

**Purpose:** first-party source code for this project's components (e.g. the Week 3 component).

**Stack:** Python 3.11+.

**Belongs here:**
- `.py` source files for whatever you're building
- `requirements.txt` (dependency manifest), once dependencies are actually needed — not created yet

**Never goes here:**
- Secrets or credentials
- Generated output
- Datasets
- Write-ups or notes (those go in `docs/`)

**Status:** active — this is where new code lands.

**Verification:**
- `python -m py_compile <file>` (or a real import) succeeds
- `ruff check src/` and `mypy src/` pass, once those tools are listed in `requirements.txt`
- Corresponding tests in `tests/` pass (see `tests/CLAUDE.md`)
