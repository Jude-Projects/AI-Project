---
name: progress-log-entry
description: Use after finishing a concrete implementation task in this repo — code, a docs deliverable, a config/infra change, or a demonstrated workflow (e.g. a Plan Mode walkthrough) — and you need to record it in PROGRESS.md before considering the task done, per this repo's established logging convention. Appends a correctly-formatted entry (task name, Date, Session ID, What changed, Verification, Notes) under the right section, using concrete verification evidence rather than restated intent. Do NOT use for pure discussion, explanation, or research that changed no file (e.g. answering a conceptual question, reading code to explain it) — PROGRESS.md logs completed work, not conversation. Do NOT use before verification evidence actually exists — wait until the change has been checked (tests pass, file compiles/opens, user confirms) before logging it.
---

# Progress Log Entry

## When this applies

Trigger: you just finished a concrete, verifiable change in this repo and need to log it.

Do not trigger on: conversational/explanatory turns with no file change, or on a task that isn't yet verified — logging happens *after* verification, never before.

## 1. Confirm there's something to log

Check that a real file actually changed this session (code, docs, config). If nothing changed, don't fabricate an entry.

## 2. Get the Session ID

Reuse the session's existing ID if one has already been established this session. Otherwise mint one in the format already used throughout this file: `CC-<YYYYMMDD>-<4 random alphanumeric chars>`.

## 3. Gather evidence before writing anything

- **What changed** — one or two concrete sentences: which files, what was added/removed/fixed.
- **Verification** — a concrete artifact: test output, a compile/open result, or "user confirmed X." Never log based on intent alone.
- **Notes** — only if there's a genuine blocker, deviation from plan, or a non-obvious decision worth remembering later. Omit the line entirely if there's nothing worth saying; don't pad it.

## 4. Re-read the tail of PROGRESS.md immediately before appending

The file may have changed since it was last read. Append after the true current last line — never anchor on a stale copy.

## 5. Append under the correct existing section

Match an existing header (e.g. `## Foundation`, `## Deep Dives`, `## Demonstrations`) if the task fits one. Only add a new section header if it genuinely doesn't.

## 6. Use the exact entry format

```markdown
- [x] <task name>
  - Date: YYYY-MM-DD
  - Session: CC-<YYYYMMDD>-<id>
  - What changed: <one or two concrete sentences>
  - Verification: <concrete evidence>
  - Notes: <only if non-obvious/blocker/deviation — omit otherwise>
```

## 7. Confirm the write

Read back just the appended lines (not the whole file) to confirm the entry landed correctly.
