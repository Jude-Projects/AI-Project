# data-quality-gate — Trigger Tests

Manual test prompts for verifying the skill fires on data-validation / publish-readiness requests and stays silent on plain SQL, dashboard-design, or metric-calculation requests.

## Should trigger the skill

1. "Validate skill-lab/orders.csv against skill-lab/quality-contract.md before it goes to the executive dashboard — should I PUBLISH or BLOCK?"
2. "Run a data quality check on quarterly_sales.csv and tell me if it's PASS, WARN, or FAIL before we load it into the report."
3. "Is the new customer export ready to publish? Check it for duplicates, missing required fields, and stale records first."

## Should NOT trigger the skill

1. "Write a SQL query that joins orders and customers and sums revenue by region."
2. "Design a new layout for the executive revenue dashboard with a KPI row and a trend chart."
3. "Calculate the month-over-month revenue growth rate from skill-lab/orders.csv."

## Expected output requirements

**For triggering prompts:**
- The data-quality-gate skill is invoked automatically (no explicit `/data-quality-gate` needed).
- Source dataset is read-only — never modified.
- Output includes a `| Check | Evidence | Status | Recommended Action |` table.
- Evidence cites concrete values (row identifiers, counts, timestamps), not vague descriptions.
- Report ends with an overall **PASS / WARN / FAIL** status and a **PUBLISH / BLOCK** recommendation.
- If a quality contract file is present, its rules are used as the source of truth; if absent, defaults are stated explicitly.

**For non-triggering prompts:**
- The skill is not invoked.
- The response directly answers the SQL, design, or metric request — no quality-check table, no PASS/WARN/FAIL, no PUBLISH/BLOCK verdict imposed on an unrelated ask.
- No dataset path or quality contract is requested, since no validation was asked for.
