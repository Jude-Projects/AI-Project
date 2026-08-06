# Pipeline Run Metadata — orders-etl

**Pipeline:** `orders-etl`
**Run ID:** `orders-etl-20260803-0200` (plus retries `-r1`, `-r2`, `-r3`)
**Scheduled trigger:** daily cron, 02:00 UTC
**Source:** `orders_raw.orders` (upstream OLTP replica)
**Target:** `warehouse.fact_orders`
**Mapping version in effect:** `v3` (deployed 2026-07-29)

## Run outcome

| Field | Value |
|---|---|
| Final status | FAILED |
| Attempts | 1 initial + 3 retries (max_retries=3, exhausted) |
| Retry backoff | exponential, base 5s (5s → 10s → 20s) |
| Rows extracted (per attempt) | 1142 |
| Rows loaded | 0 |
| Total duration | 48,210 ms |
| Alert dispatched | Yes — `#data-eng-alerts`, 2026-08-03T02:00:50Z |

## Recent change log (upstream + mapping)

- **2026-07-29:** `region` mapping bumped to `v3`. Enum allow-list: `{US-East, US-West, EU-Central, EU-West, APAC}`. Fallback rule for unmapped values: set to `NULL` (previous `v2` behavior was to pass the raw string through unmapped).
- **2026-07-31:** Upstream OLTP team enabled a new signup flow for the `LATAM-BR` sales region (per `#sales-ops` announcement, not yet reflected in `orders-etl` mapping config).
- **2026-08-01:** `warehouse.fact_orders.region` column constraint tightened to `NOT NULL` as part of the executive dashboard data-quality initiative (ties to `skill-lab/quality-contract.md`).

## Known-good baseline

Last successful run: `orders-etl-20260802-0200`, rows_loaded=1098, duration_ms=6340, no warnings.

## Things NOT yet confirmed

- Whether `LATAM-BR` is the only unmapped enum value in the current extract, or one of several.
- Whether the 37 NULL rows are all `LATAM-BR`, or include other causes (extract-side nulls, upstream nulls).
- Whether the `NOT NULL` constraint change on 2026-08-01 was communicated to the `orders-etl` pipeline owner before it went live.
