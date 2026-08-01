# AI-Project Architecture

**Status:** Foundation approved 2026-07-30. No product requirements exist yet — this document records only the folder structure approved so far, not a product design.

## Overview

This repo is a personal workspace for coursework and experiments (see root `README.md`). The first known deliverable is a "Week 3" component, confirmed to be code, which will live in `src/`.

## Note on root CLAUDE.md

The root `CLAUDE.md` in this repository describes an unrelated project ("Colaberry Agent Project") — a Node/Express/React stack, telemetry contracts, Mandrill/Basecamp/OpenClaw integrations, a named DRI, production infrastructure. None of that applies to this repo, and it was confirmed by the project owner not to be this project's definition.

It is left in place untouched (protected) rather than rewritten or deleted — that is a separate decision outside the scope of this approval. Two mechanics only were deliberately borrowed from it for this repo, per explicit instruction:

1. The subdirectory-`CLAUDE.md`-per-folder pattern (each major folder documents its own conventions).
2. The `PROGRESS.md` entry format and session-ID scheme.

No other rule from root `CLAUDE.md` (testing pyramid, idempotency, telemetry, security posture, etc.) governs this repo.

## Approved tree

```
AI-Project/
├── CLAUDE.md          [EXISTING — protected, unrelated project, do not touch]
├── README.md          [EXISTING]
├── PROGRESS.md        [EXISTING]
├── .claude/
│   ├── agents/        [EXISTING — protected, Claude Code harness tooling]
│   ├── CLAUDE.md      [NEW]
│   └── README.md      [NEW]
├── src/
│   ├── CLAUDE.md      [NEW]
│   └── README.md      [NEW]
├── tests/
│   ├── CLAUDE.md      [NEW]
│   └── README.md      [NEW]
├── docs/
│   ├── CLAUDE.md      [NEW]
│   ├── README.md      [NEW]
│   └── ARCHITECTURE.md [NEW — this file]
├── data/              [NOT CREATED — deferred, no confirmed need]
└── notebooks/         [NOT CREATED — deferred, no confirmed need]
```

## Per-folder record

| Folder | Purpose | Belongs | Never | Status | Verification |
|---|---|---|---|---|---|
| `src/` | First-party source code | `.py` source files, `requirements.txt` once needed | Secrets, generated output, datasets, write-ups | Active | `python -m py_compile` / import succeeds; `ruff check src/` + `mypy src/` once added |
| `tests/` | Automated tests mirroring `src/` | `test_*.py` files, fixtures | Production code, scratch experiments | Scaffolded, empty | `pytest` exits 0 |
| `docs/` | Written material — write-ups, notes, diagrams | Markdown/PDF docs | Source code, secrets, generated artifacts | Active (this file lives here) | Markdown renders cleanly, no broken links |
| `.claude/` | Claude Code harness config | Agent definitions, harness settings | Project source or data | Protected — do not touch unless deliberately configuring the harness | N/A until an agent/setting is added |
| `data/` | Local datasets/sample inputs, if ever needed | Small local data files | Credentials, large/sensitive files | Deferred, not created | N/A |
| `notebooks/` | Jupyter notebooks, if the stack uses them | `.ipynb` files | Production logic (belongs in `src/`) | Deferred, not created | N/A |

## Traceability

| Folder | Driven by |
|---|---|
| `src/`, `tests/`, `docs/` | Existing empty scaffold + general software-project convention |
| `.claude/` | Claude Code harness convention (not a project rule) |
| `data/`, `notebooks/` | Speculative only — not created |
| Root `CLAUDE.md` | Out of scope; protected, unrelated project |

## Assumptions

1. "Coursework/experiments" implies discrete weekly components; format (code vs. notebook vs. report) is confirmed code-based only for Week 3 so far.
2. Root `CLAUDE.md`'s substantive rules (backend/frontend layout, testing pyramid, idempotency, telemetry, security posture) do not apply to this repo.
3. Stack (Python 3.11+ / pytest / ruff / mypy) was a recommendation from Claude, chosen by the project owner from a short list — not derived from an external course requirement, since none has been provided.

## Decision log

- 2026-07-30 — Proposed folder-tree architecture (folders, per-folder rules, traceability, assumptions).
- 2026-07-30 — Architecture approved by project owner.
- 2026-07-30 — Foundation approved: added `README.md` to each new major folder (`src/`, `tests/`, `docs/`, `.claude/`) and this architecture document. No product code written, no dependencies installed. `data/` and `notebooks/` intentionally left uncreated.
- 2026-07-30 — Stack decided: Python 3.11+, `pytest`, `ruff`, `mypy`. `src/CLAUDE.md` and `tests/CLAUDE.md` updated with concrete verification commands. No dependencies installed yet — `requirements.txt` not yet created.

## Open items

- `requirements.txt` — not yet created; add when the Week 3 component actually needs a dependency (or `pytest`/`ruff`/`mypy` themselves).
- Whether/when `data/` or `notebooks/` get created — deferred until an actual need appears.
- Whether root `CLAUDE.md` is ever rewritten or replaced for this project — separate decision, not part of this approval.
