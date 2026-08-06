---
name: executive-dashboard-brief
description: Use when the user asks to turn a data-quality result, failed refresh, pipeline incident, KPI variance, or technical investigation into an executive dashboard update. Produces a concise leadership brief containing status, business impact, verified evidence, decision needed, owner, and next update time.
---

# Executive Dashboard Brief

## 1. Require a source report

Use the supplied quality report(s) and/or triage report(s) (e.g. a data-quality-gate report, an etl-failure-triage report) as the only source of facts. Do not proceed without at least one concrete source document — this skill summarizes existing findings for leadership, it does not perform new investigation.

## 2. Separate verified facts from unresolved questions

Everything in **What We Know** must trace directly back to something stated in the source report(s) (a PASS/WARN/FAIL result, a cited piece of evidence, a ranked cause). Everything genuinely uncertain, unconfirmed, or still open in the source report(s) goes in **What We Do Not Know** — do not resolve open questions on the brief's behalf.

## 3. Never invent

Never invent or estimate a financial/business impact, a root cause, an owner, or a timing commitment that isn't stated in the source material. If the source report doesn't name one of these, say so explicitly (e.g. "Owner: not yet assigned — needs designation") rather than filling in a plausible-sounding value.

## 4. Strip technical detail

Leave out raw logs, stack traces, SQL, file paths, and implementation-level detail. Translate technical findings (e.g. "NOT NULL constraint violated on region column") into business terms (e.g. "38 orders can't be attributed to a sales region").

## 5. State dashboard status explicitly

Always state plainly whether the dashboard/report should remain blocked, is cleared to publish, or is publishing with caveats — carried directly from the source report's PUBLISH/BLOCK (or equivalent) verdict. Never soften a BLOCK into an implied "mostly fine."

## 6. Use template.md for structure

Read `template.md` in this skill's directory and fill in its exact structure — do not add, remove, reorder, or rename its sections.

## Output

Return exactly the sections in `template.md`: Status, Business Impact, What We Know, What We Do Not Know, Decision or Action Needed, Owner, Next Update. Keep each section short — a leadership brief, not a report.

## Constraints

- Source facts only — no new investigation, no invented figures, causes, owners, or dates.
- No raw logs or unnecessary technical detail.
- Dashboard block/publish status must be stated explicitly and must match the source report's verdict.
