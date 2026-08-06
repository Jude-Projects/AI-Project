# Quality Checks Reference

Full definition of each check run by the data-quality-gate skill, the evidence each check requires, and the default thresholds to use when the quality contract doesn't specify one. Read this before running checks — do not guess at check definitions from memory.

## Schema
Expected columns are present and hold the correct type (string/number/date/etc.). If the contract names a field (e.g. `region`) and the dataset has a differently-named column that appears to serve the same purpose (e.g. `customer_region`), do not silently treat them as identical — flag the naming mismatch as WARN so the downstream mapping can be confirmed, even if the check otherwise passes.

**Default if contract is silent:** no default — schema can only be checked against columns the contract or an explicit user instruction names.

## Freshness
The dataset's load/updated timestamp compared against the contract's max-age threshold, measured from the validation time.

**Default if contract is silent:** max age of 24 hours.

**Evidence required:** the specific row(s) or timestamp that violates the threshold, and how old it is (e.g. "`ORD-1009`: `load_timestamp` 2026-07-31T14:00:00Z, ~3 days before validation date").

## Expected volume
Row count compared against the contract's minimum (and maximum, if given).

**Default if contract is silent:** minimum 1 row (i.e. flag an empty dataset); no maximum.

**Evidence required:** the actual row count.

## Key uniqueness
No duplicate values in the designated key column(s) (e.g. `order_id`).

**Default if contract is silent:** use the most obvious identifier column (a column named `*_id`, `id`, or the first column) as the key.

**Evidence required:** the specific duplicated key value(s) and the row numbers/lines they appear on.

## Duplicates
No fully duplicate rows (every column matches another row exactly).

**Evidence required:** the row numbers/lines and enough of the row content to confirm the match.

## Required fields
No missing/empty values in fields the contract marks required.

**Evidence required:** the specific row identifier(s) with the missing value and which field is empty.

## Nulls
Null/empty rates in non-required fields, flagged if abnormal (e.g. a field that's usually populated but is empty in a large fraction of rows).

**Default if contract is silent:** flag as WARN if more than ~20% of a non-required field's values are empty; this is a heuristic, not a hard rule — use judgment based on what the field represents.

## Numeric rules
Values respect contract-defined bounds (e.g. revenue greater than zero, a percentage between 0 and 100).

**Evidence required:** the specific row identifier(s) and the out-of-bounds value.

## General evidence standard

Every check's evidence must cite something concrete and checkable — a row identifier, a count, a timestamp, a value. "Some rows look off" or "data appears mostly clean" is not acceptable evidence; if a check can't be backed by a specific citation, it hasn't actually been run.
