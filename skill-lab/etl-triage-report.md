# ETL Failure Triage Report — orders-etl

**Log:** `skill-lab/orders-pipeline-failure.log`
**Metadata:** `skill-lab/pipeline-run-metadata.md`
**Investigated:** 2026-08-03 (read-only; pipeline not changed, job not rerun)

## 1. Incident Summary

The `orders-etl` scheduled load (`run_id=orders-etl-20260803-0200`) failed at 2026-08-03T02:00 UTC and exhausted all 3 configured retries before aborting. Every attempt extracted the same 1,142 rows successfully but failed at the transform stage with a `SchemaValidationError` on `warehouse.fact_orders.region` (NOT NULL constraint violated by 37 rows). Final status: **FAILED**, `rows_loaded=0`, total duration 48,210 ms. An alert was dispatched to `#data-eng-alerts`.

## 2. Evidence

- Log: `applying column mapping: customer_region -> region (mapping_version=v3)` — mapping v3 in effect on all 4 attempts.
- Log: `mapping v3 expected enum region in {US-East,US-West,EU-Central,EU-West,APAC}; encountered unmapped value "LATAM-BR" at source row offset 812` — an out-of-enum region value.
- Log: `unmapped region value "LATAM-BR" defaulted to NULL by mapping v3 fallback rule` — the mapping's fallback silently nulls unmapped values instead of failing loudly or passing them through.
- Log: `schema validation failed on target column warehouse.fact_orders.region: NOT NULL constraint violated, 37 rows have region=NULL after mapping` — the NULLed rows collide with a NOT NULL constraint on the target.
- Log: identical `SchemaValidationError` (same message, same `rows_extracted=1142`) on the initial attempt and all 3 retries (`r1`, `r2`, `r3`).
- Log: `max_retries (3) exhausted, aborting ... final_status=FAILED, rows_loaded=0`.
- Metadata: mapping `v3` deployed **2026-07-29**; its fallback rule for unmapped values is "set to NULL" (previous `v2` behavior passed the raw string through unmapped).
- Metadata: **2026-07-31** — upstream OLTP team enabled a new `LATAM-BR` sales region, "not yet reflected in `orders-etl` mapping config."
- Metadata: **2026-08-01** — `warehouse.fact_orders.region` constraint tightened to `NOT NULL` as part of the executive dashboard data-quality initiative.
- Metadata: last successful run `orders-etl-20260802-0200` — `rows_loaded=1098`, no warnings, i.e. the failure is new as of the 08-03 run, consistent with the constraint change landing 08-01 and the pipeline running again on schedule.

## 3. Ranked Causes

**1. Schema mismatch: unmapped `LATAM-BR` region value collides with a new NOT NULL constraint — fact-confirmed**
The mapping v3 enum doesn't include `LATAM-BR` (added upstream 2026-07-31, metadata explicitly notes it's "not yet reflected" in the mapping). The fallback rule nulls unmapped values, and those NULLs then violate the NOT NULL constraint added to `warehouse.fact_orders.region` on 2026-08-01. Every fact — the WARN line, the ERROR line, and both change-log entries — points at the same chain of events with matching dates and column name.

**2. Contributing factor: mapping v3's silent-null fallback masks the real gap — fact-confirmed**
The fallback rule change from v2 (pass raw string through) to v3 (default to NULL) is itself a design choice that converts an unmapped value into a silent data-loss event rather than a loud, immediate failure at the mapping step. Without the 08-01 NOT NULL constraint, this would have kept loading successfully with silently-NULLed regions — the constraint is what surfaced an existing latent problem.

**3. Retries were futile because the failure is deterministic, not transient — fact-confirmed, explains "retry did not resolve"**
All 4 attempts (initial + 3 retries) produced byte-identical errors and identical `rows_extracted=1142`, ruling out a transient cause (network blip, lock contention). This confirms the retry mechanism could not have fixed this failure class — the fix has to happen in the mapping config or the constraint, not by rerunning.

**4. Open question: whether 37 NULL rows are all `LATAM-BR`, or include other unmapped values — hypothesis, not yet confirmed**
The log surfaces only one example WARN (`offset 812`, value `LATAM-BR`), but 37 rows ended up NULL. Metadata explicitly lists this as an unconfirmed item. It's possible the log only prints a sample of unmapped-value warnings rather than one per row, or that other unmapped values are also present — the current evidence doesn't distinguish these.

## 4. Next Tests

For cause 1 (schema mismatch): Pull the full set of unmapped-value warnings (or query the raw extract directly) for `orders_raw.orders` filtered to rows where `customer_region` is not in the v3 enum allow-list, and confirm all 37 NULL rows trace back to `LATAM-BR` specifically.

For cause 2 (fallback rule): Review the mapping v3 config/changelog to confirm the fallback behavior is "default to NULL" as stated, and check whether this fallback is documented/intentional or an unreviewed regression from v2's passthrough behavior.

For cause 3 (retry futility): No further test needed — already confirmed by the identical error signature across all 4 attempts. Included here only to rule out a transient-cause explanation.

For cause 4 (open question on NULL row count): Cross-reference the 37 NULL rows in the failed transform's staging output (if retained) against the full list of source `customer_region` values present in this extract, to see whether any value besides `LATAM-BR` is also unmapped.

## 5. Escalation Recommendation

**Escalate now**, to the `orders-etl` pipeline owner and the owner of the `warehouse.fact_orders` schema/constraint change. Two independent teams made uncoordinated changes that only collided in production: the region enum expansion (upstream OLTP, 2026-07-31) and the NOT NULL tightening (data-quality initiative, 2026-08-01), with neither apparently checked against the other before the NOT NULL constraint went live. This is a repeated failure (3/3 retries exhausted) with a clear root-cause chain but requires an owner decision on the fix — add `LATAM-BR` to the mapping enum, change the fallback behavior, or relax/delay the constraint — none of which this triage is authorized to make.

*Note: the root `CLAUDE.md`'s specific escalation mechanics (`/tmp/escalation.json`, Mandrill notification) belong to an unrelated project per `.claude/CLAUDE.md` and don't apply to this repo; the recommendation above is a plain escalate-to-owner call, not that specific protocol.*
