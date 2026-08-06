# Common ETL/ELT Failure Patterns Reference

Patterns to check for when triaging a pipeline failure, what evidence each leaves in logs/metadata, and the safe next diagnostic step. Use this to recognize a pattern in the log — never assume a pattern applies without a matching log line or metadata fact.

## Schema mismatch (column, type, or enum)

**Signature in logs:** `SchemaValidationError`, `NOT NULL constraint`, `type mismatch`, `unmapped value`, `column 'X' violates`.

**Common root causes:** upstream added/renamed a column, a new enum/category value appeared that the mapping layer doesn't recognize, a constraint was tightened on the target without updating the pipeline.

**Next safe diagnostic step:** find the exact unmapped value(s) and how many rows they affect; check whether the mapping config or the target schema changed most recently (whichever changed last is the more likely trigger); do not edit the mapping or schema — report the finding.

## Failed conversion or mapping step

**Signature in logs:** `mapping vN`, `fallback rule`, `defaulted to NULL`, `cast failed`, `ValueError` during transform.

**Common root causes:** a mapping/lookup table is out of date relative to upstream source values; a fallback rule silently nulls or drops data instead of failing loudly, masking data loss until a downstream constraint catches it.

**Next safe diagnostic step:** identify the mapping version in effect and its last-updated date; compare against any upstream change log entries after that date; flag if the fallback behavior (e.g. "default to NULL") is itself contributing to the failure.

## Retry exhaustion without resolution

**Signature in logs:** repeated identical error across `retry 1/N`, `retry 2/N`, ... up to `max_retries exhausted`, with the same error signature on every attempt.

**Common root causes:** the failure is deterministic (bad data, bad config, bad schema) rather than transient (network blip, lock contention, rate limit) — retries only help transient failures, so identical errors across all retries indicate the retry mechanism is not addressing the actual cause.

**Next safe diagnostic step:** confirm the error signature is byte-for-byte identical across attempts (if so, this rules out transient/flaky causes and points at a persistent upstream/config issue); do not increase retry count or rerun — that will reproduce the same failure.

## Upstream data volume anomaly

**Signature in logs:** `rows_extracted` far above or below the historical baseline; empty extract; extract step succeeds but transform/load rejects most/all rows.

**Common root causes:** upstream backfill or bulk delete, a filter/watermark bug, a partial upstream outage.

**Next safe diagnostic step:** compare `rows_extracted` against the last known-good run's row count; check the watermark/incremental-load boundary for correctness.

## Downstream constraint change

**Signature in logs:** a previously-passing schema validation now fails with no corresponding change in the source data pattern.

**Common root causes:** a DDL change on the target table (new constraint, new NOT NULL, new foreign key) that wasn't communicated to pipeline owners.

**Next safe diagnostic step:** check run metadata / change log for target-schema DDL changes near the failure date; correlate the DDL change date against the first failing run.

## Credential / connectivity failure

**Signature in logs:** `AuthenticationError`, `connection refused`, `timeout`, failure at the extract stage before any rows are processed.

**Common root causes:** rotated credentials not propagated to the pipeline's secret store, network/firewall change, upstream service outage.

**Next safe diagnostic step:** check whether the failure occurs before any rows are extracted (points to connectivity/auth) vs. after extraction succeeds (points to data/schema); do not attempt to reconnect or rerun.

## General triage discipline

- A **fact** is something directly stated in the log or metadata (an error string, a row count, a timestamp, a config value).
- A **hypothesis** is an inference connecting facts to a probable cause. Always label it as such and say what evidence would confirm or rule it out.
- Never state a root cause as certain unless the log/metadata contains direct, unambiguous confirmation (e.g. a stack trace naming the exact failing assertion). Otherwise, rank it as a likely cause with a confidence-appropriate next test.
