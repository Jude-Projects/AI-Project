# tests/ — conventions

Note: the root `CLAUDE.md` describes an unrelated project (Colaberry). It does not apply here. This file is the actual convention for this folder.

**Purpose:** automated tests mirroring whatever lands in `src/`.

**Stack:** Python 3.11+, `pytest`.

**Belongs here:**
- Test files named `test_*.py` (pytest convention)
- Test fixtures

**Never goes here:**
- Production or source code (that goes in `src/`)
- Scratch experiments

**Status:** scaffolded, currently empty — ready for test files once `src/` has code to test.

**Verification:** `pytest` (run from repo root) exits 0.
