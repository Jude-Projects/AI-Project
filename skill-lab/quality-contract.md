# Quality Contract — orders dataset

- **order_id**: must be unique (no duplicate order IDs).
- **region**: required on every row (no missing/null values).
- **revenue**: must be greater than zero (no negative or zero revenue).
- **load_timestamp**: must be less than 24 hours old at validation time.
- **row count**: expected at least 10 rows.
