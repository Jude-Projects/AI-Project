---
name: etl-failure-triage
description: Use when the user asks why an ETL or ELT pipeline, scheduled load, SQL job, data refresh, or ingestion process failed or produced suspicious output. Reviews logs and run metadata, ranks likely causes, cites evidence, and recommends the next safe diagnostic steps.
---

# ETL Failure Triage

## 1. Require a log, run output, or failure description

Ask for (or use the supplied) failure log, run output, or a description of the failure. Do not proceed without concrete evidence to work from — do not triage from a vague symptom alone (e.g. "the dashboard looks wrong") without a log or run artifact.

## 2. Read run metadata when supplied

If a run-metadata file (config, change log, known-good baseline, schema/mapping version history) is supplied or referenced, read it in full before ranking causes. Metadata often contains the fact (a recent schema or mapping change) that turns a hypothesis into a confirmed cause.

## 3. Recognize failure patterns

Read `references/common-failures.md` before ranking causes — it catalogs common ETL/ELT failure signatures (schema mismatch, failed conversion/mapping, retry exhaustion, volume anomaly, downstream constraint change, credential/connectivity failure), what evidence each leaves in logs, and the safe next diagnostic step for each. Match what you find in the log/metadata against these patterns; do not invent a pattern that isn't evidenced.

## 4. Separate facts from hypotheses

A **fact** is directly stated in the log or metadata (an error string, a row count, a timestamp, a config value, a change-log entry). A **hypothesis** is an inference connecting facts to a probable cause — always label it as such.

## 5. Cite evidence for every likely cause

Every ranked cause must point to a specific log line or metadata fact. No cause without a citation.

## 6. Rank the most likely causes

Order causes by how directly the evidence supports them — a cause confirmed by an explicit error message outranks one inferred from timing correlation alone.

## 7. Provide the next diagnostic step for each cause

For every ranked cause, state the next safe action that would confirm or rule it out (see `references/common-failures.md` for the standard next step per pattern).

## Report format

Return exactly these sections:

1. **Incident Summary** — what failed, when, final status, in 2-3 sentences.
2. **Evidence** — the concrete facts pulled from the log/metadata (quote or closely paraphrase the relevant lines).
3. **Ranked Causes** — ordered list, each with its supporting evidence and confidence (fact-confirmed vs. hypothesis).
4. **Next Tests** — the safe diagnostic step for each ranked cause.
5. **Escalation Recommendation** — whether this needs human/owner escalation now, and to whom, based on the Autonomy Model / Escalation Protocol in the root `CLAUDE.md` if this repo has one.

## Constraints

- Do not change pipeline code, mapping configs, or schemas.
- Do not rerun jobs.
- Do not claim a root cause without direct evidence — rank it as a hypothesis instead and say what would confirm it.
