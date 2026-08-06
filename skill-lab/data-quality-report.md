# Data Quality Report — orders.csv

**Dataset:** `skill-lab/orders.csv`
**Contract:** `skill-lab/quality-contract.md`
**Validated:** 2026-08-03 (read-only inspection; source file not modified)

| Check | Evidence | Status | Recommended Action |
|---|---|---|---|
| Schema | Contract fields `region`/`revenue` are present in the CSV only under different names: `customer_region`, `revenue_usd`. `order_id` and `load_timestamp` match exactly. | WARN | Confirm the dashboard ingest maps `customer_region`→region and `revenue_usd`→revenue explicitly; align naming or document the mapping to prevent silent breakage if the pipeline expects exact contract field names. |
| Freshness (<24h) | `ORD-1009` has `load_timestamp = 2026-07-31T14:00:00Z`, ~3 days before validation date (2026-08-03) — exceeds the 24-hour max-age threshold. All other rows are timestamped 2026-08-03 (09:15–14:00Z) and are within threshold. | FAIL | Re-extract/re-load `ORD-1009` (or exclude it) before publishing so all rows meet the freshness contract. |
| Expected volume (≥10 rows) | 12 data rows present (`ORD-1001`–`ORD-1011`, with `ORD-1010` listed twice). | PASS | None. |
| Key uniqueness (`order_id`) | `ORD-1010` appears twice, at rows 11 and 12. | FAIL | Deduplicate on `order_id`; investigate upstream source for why the same order was emitted twice. |
| Duplicate rows | Rows 11 and 12 are fully identical (`ORD-1010,2026-08-02,EU-Central,267.30,2026-08-03T13:15:00Z`). | FAIL | Remove the exact-duplicate row before load. |
| Required field: region | Row for `ORD-1004` has an empty `customer_region` value. | FAIL | Backfill or reject `ORD-1004` — region is a required field per contract. |
| Numeric rule: revenue > 0 | `ORD-1006` has `revenue_usd = -55.00`. | FAIL | Investigate the negative revenue value (likely a refund/return miscoded as a sale) and correct or exclude before publishing. |

## Verdict

**Overall status: FAIL** (5 of 7 checks failed or warned; 4 hard FAILs)

**Recommendation: BLOCK**

Do not publish to the executive revenue dashboard until: the duplicate `ORD-1010` row is removed, `ORD-1004`'s missing region is resolved, `ORD-1006`'s negative revenue is corrected or excluded, and the stale `ORD-1009` record is refreshed or dropped. The schema naming mismatch (WARN) should also be confirmed with the ingest pipeline owner.
