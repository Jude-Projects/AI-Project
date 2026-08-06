---
name: data-quality-gate
description: Use when the user explicitly asks to validate a dataset, CSV, ETL output, or query result against a quality contract, or asks whether data is safe/ready to publish to a dashboard or report (e.g. "validate this before it goes live", "is this dataset PASS or FAIL", "should we publish or block this data"). Checks the data against a quality contract and returns PASS, WARN, or FAIL with evidence and a PUBLISH or BLOCK recommendation. Do NOT use for ordinary requests to write or debug SQL, calculate/define a metric, or design a dashboard's layout or visuals — those alone are not data-validation or publish-readiness requests, even if the data involved is the same dataset. Only invoke when the user is asking for a quality/readiness verdict on data, not when they're asking you to query, compute, or visualize it.
---

# Data Quality Gate

## When this applies

Trigger: the user wants a validation/readiness verdict on a dataset — "validate X", "is this ready to publish", "check this against the quality contract", "PASS/WARN/FAIL this data", "PUBLISH or BLOCK".

Do not trigger on requests that only involve writing SQL, computing a metric, or designing/laying out a dashboard — even against the same file — unless the user also asks for a quality check or a publish/block verdict.

## 1. Require a dataset path

Ask for (or use the supplied) path to the dataset to validate. Do not proceed without a concrete path. Never modify the source data — read-only inspection only.

## 2. Load the quality contract

Look for a supplied quality contract (e.g. a `quality-contract.md` or similar file in the same directory or explicitly referenced). If one exists, use its rules as the source of truth for thresholds. If none is supplied, fall back to sane defaults and state clearly that defaults were used.

## 3. Run the checks

Before evaluating, **read `references/quality-checks.md`** — it defines each check (schema, freshness, expected volume, key uniqueness, duplicates, required fields, nulls, numeric rules), the evidence each one requires, and the default threshold to use when the contract is silent on that check. Run every check listed there against the dataset, using the contract's specific rules where provided.

## 4. Report results

Return a table with these columns:

| Check | Evidence | Status | Recommended Action |
|---|---|---|---|

- **Evidence** must cite concrete values (row identifiers, counts, timestamps) — never a vague description.
- **Status** is PASS, WARN, or FAIL per row.

## 5. Finish with a verdict

End the report with:
1. An overall dataset status: **PASS**, **WARN**, or **FAIL**.
2. A recommendation: **PUBLISH** or **BLOCK**.

FAIL on any check → overall FAIL → BLOCK. WARN-only (no FAIL) → overall WARN → BLOCK unless the user explicitly accepts the risk. All checks clean → PASS → PUBLISH.

## Constraints

- Never modify, delete, or reformat the source dataset. This skill inspects; it does not clean.
- Keep the report concise and procedural — table plus verdict, no narrative padding.
