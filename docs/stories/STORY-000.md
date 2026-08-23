# STORY-000 — Build the Command Center

## Narrative

As the builder of the AI Data Assistant project, I want a single Command Center page that shows what is being built, what it is meant to move, and how far along it is, so that I (and anyone I show it to) can see real project state at a glance instead of hunting through files.

## Where it lives

Entry point: `index.html` at the repo root. Supporting assets under `assets/`.

## Acceptance criteria (word for word — matched by text in `.colaberry/progress.json`)

1. Given the Command Center, when it is opened, then every tab is reachable and every card drills down one level.
2. Given sample mode, when any tab is shown, then the sample data is visibly labelled as sample.
3. Given the Command Center, when any tab renders, then .colaberry/plan.json and .colaberry/progress.json are both committed in this repo and every tab reads its content from them at runtime rather than from hard-coded values.
4. Given the Command Center, when any tab is shown, then .colaberry/manifest.json is committed in this repo and every tab shows how old that data is and warns when the age exceeds a week.
5. Trust — no tab shows a number, a connection or a result the project has not actually produced.

## Verification

Tracked in `.colaberry/progress.json` under `stories[].id == "STORY-000"` as a `criteria[]` array of `{ text, passed }`. A criterion is only set `passed: true` once it is genuinely true in the repo, confirmed by reading the code — not because the rest of the story looks finished.

## Status

Build in progress. See `PROGRESS.md` for session-by-session detail.
