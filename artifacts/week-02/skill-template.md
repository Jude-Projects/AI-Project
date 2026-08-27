# Skill Template — Fill-In-The-Blanks Guide

*A reusable starting point for writing a new Skill. No coding experience required. Read the explanations, then fill in the bracketed placeholders with your own words.*

---

## First, in plain English: what is a Skill?

A Skill is a **written instruction sheet** that an AI assistant picks up *only when it's relevant*, and ignores the rest of the time.

Think of a huge filing cabinet full of folders, one per Skill. Taped to the front of each folder is a small index card describing what's inside and when to use it. The assistant doesn't open every folder for every request — it scans the index cards, and only pulls out the folder that matches. That index card is called the **description**, and it lives in a section called the **frontmatter**. The rest of the folder — the actual step-by-step instructions — is called the **instruction body**, and it only gets read once the right folder has been pulled.

That's the whole idea. Everything below is just helping you write a good index card (frontmatter) and a good set of instructions (body).

---

## Before you start: answer these 3 questions on scratch paper

You'll reuse your answers throughout this template, so it helps to think them through first.

1. **What task do you want handled the same way, every time?**
   *(e.g. "writing a weekly status update," "checking a document for spelling and tone before it goes out," "formatting meeting notes into action items")*

2. **What would you actually type or say when you want this done?**
   List 2–3 real phrasings you'd naturally use.

3. **What similar-sounding request should NOT trigger this?**
   Think of a request that mentions the same topic but wants something different.
   *(e.g. your Skill is "format meeting notes into action items" — a request to "summarize what was discussed" is similar but different, and should NOT trigger it)*

Question 3 is the one people skip, and it's the one that matters most. Keep reading and you'll see why.

---

## SECTION 1 — Frontmatter (the index card)

Copy this block exactly, including the lines of three dashes (`---`) above and below it. This is the part that is *always* scanned, for *every* request, so it has to do a lot of work in a small space.

```yaml
---
name: [short-name-with-dashes]
description: [see Section 2 below — this is the most important field in the whole document]
---
```

### `name` — explained

This is just the label on the folder. It has one job: let you and the assistant both refer to this Skill unambiguously.

**Rules of thumb:**
- Use lowercase words separated by dashes, no spaces: `meeting-notes-formatter`, not `Meeting Notes Formatter`.
- Keep it short — 2 to 4 words.
- Make it describe the *task*, not the *topic*. `expense-report-builder` is better than `finance-helper` (too broad, doesn't say what it does).

**Fill in your own:**
```
name: [your-task-name-here]
```

### `description` — explained

This single field decides whether your Skill ever gets used, and whether it gets used *correctly*. It is read every time, for every request, before anything else in the document. Everything else in this template only matters after the description has already done its job.

A weak description causes one of two failures:
- **Too vague → it fires on the wrong requests.** ("For document stuff" would trigger on almost anything involving a file.)
- **Too narrow or unclear → it never fires when it should.** (Only mentioning one exact phrase means a slightly different but equally valid request gets missed.)

The fix for both problems is the same: write the description as three distinct parts. See Section 2 — it walks through writing this field slowly, with a fill-in-the-blank worksheet, because it's worth the extra care.

---

## SECTION 2 — Writing an effective description (worksheet)

A good description always has three parts. Write each one as a complete sentence, then combine them into a single paragraph for the `description:` field.

### Part A — When TO use it (the positive trigger)

Start with the word **"Use when"** and describe the real-world situation, not just a keyword. Use the phrasings you wrote down in the "before you start" section.

```
Use when [the situation that should trigger this Skill — describe the
person's goal, not just a topic]. For example: "[example phrase 1]",
"[example phrase 2]".
```

*Filled-in example (from a real Skill in this project):*
> "Use when the user explicitly asks to validate a dataset, CSV, ETL output, or query result against a quality contract, or asks whether data is safe/ready to publish to a dashboard or report (e.g. 'validate this before it goes live', 'is this dataset PASS or FAIL')."

### Part B — What it actually does (the summary)

One or two plain sentences. No jargon — write it the way you'd explain it to a coworker in the hallway.

```
[Does X, then Y, and produces Z as the result.]
```

*Filled-in example:*
> "Checks the data against a quality contract and returns PASS, WARN, or FAIL with evidence and a PUBLISH or BLOCK recommendation."

### Part C — When NOT to use it (the negative trigger)

This is the part most people forget, and it's the difference between a Skill that works reliably and one that misfires. Think back to Question 3 from "before you start": what's the nearby request that should be handled normally instead?

```
Do NOT use for [the similar-but-different request]. Only invoke when
[the one specific condition that must be true].
```

*Filled-in example:*
> "Do NOT use for ordinary requests to write or debug SQL, calculate/define a metric, or design a dashboard's layout or visuals — those alone are not data-validation requests, even if the data involved is the same dataset."

### Put it together

```
description: Use when [situation] (e.g. "[phrase]", "[phrase]"). [What it
does, in one or two sentences]. Do NOT use for [similar-but-different
request] — [why it's different]. Only invoke when [the specific condition].
```

### Self-test before moving on

Read your combined description out loud and ask:
- [ ] Could a stranger tell *exactly* when to use this, just from reading it?
- [ ] Does it name at least one thing this Skill should **not** be used for?
- [ ] Did you avoid vague words like "helps with," "related to," or "stuff"?

If any box is unchecked, rewrite that part before moving on — everything below this point only works if the description is solid.

---

## SECTION 3 — Instruction body (the actual playbook)

This is everything that comes *after* the frontmatter's closing `---`. It only gets read once the description has already matched, so it's safe to be as detailed as the task needs — write it like instructions for a capable new person who has never done this task before and won't get to ask follow-up questions.

### Template

```markdown
# [Your Skill's Title, in Plain Words]

## When this applies

Restate, briefly, the situation from your description (Part A) and the
exclusion from Part C. This is a quick reminder for anyone reading the
full document later.

## Step 1 — [First thing to check or gather]

[Plain instructions. If something is required before continuing —
like a file, a piece of information, or a confirmation — say so clearly,
and say what to do if it's missing.]

## Step 2 — [Next action]

[Instructions. Be specific: exact wording, exact format, exact order —
don't leave room for guessing.]

## Step 3 — [Next action]

[Continue numbering steps for as long as the task actually needs.
A short task might only need 2–3 steps; a complex one might need 7–8.
Don't pad it, and don't compress it.]

## Output format

[Exactly what the final result should look like — a table with named
columns, a specific list format, a required closing line, etc. Being
explicit here is what makes the output consistent every time.]
```

### Tips for writing clear steps

- **Write in imperative sentences** ("Check the file exists," not "The file should be checked").
- **Name the exact format for anything structured** — a table, a checklist, specific headings — rather than leaving formatting up to guesswork each time.
- **Call out what to do when something's missing or ambiguous.** ("If no specific quality contract is supplied, fall back to a listed default and say so clearly" is far better than silence on the topic.)
- **If a step needs a lot of reference detail** (long lists of rules, a big table of options), consider putting that detail in a *separate* file and pointing to it only at the step that needs it — that keeps the main instructions easy to scan.

---

## Full worked example (for reference)

Here is a complete, real Skill built from this exact template, so you can see the finished shape:

```yaml
---
name: progress-log-entry
description: Use after finishing a concrete implementation task in this
repo — code, a docs deliverable, a config/infra change, or a demonstrated
workflow — and you need to record it in a progress log before considering
the task done. Appends a correctly-formatted entry (task name, date,
session ID, what changed, verification, notes) under the right section,
using concrete verification evidence rather than restated intent. Do NOT
use for pure discussion or research that changed no file. Do NOT use
before verification evidence actually exists — wait until the change has
been checked before logging it.
---

# Progress Log Entry

## When this applies

Trigger: you just finished a concrete, verifiable change and need to log
it. Do not trigger on conversational turns with no file change, or before
the change is verified.

## Step 1 — Confirm there's something to log

Check that a real file actually changed. If nothing changed, don't
fabricate an entry.

## Step 2 — Gather evidence

Write down: what changed (concretely), how it was verified (a real test
result or confirmation — not just a restated plan), and any non-obvious
notes worth remembering later.

## Step 3 — Append the entry

Add it to the log using the required format, under the matching section.

## Output format

- [x] <task name>
  - Date: <date>
  - What changed: <concrete summary>
  - Verification: <concrete evidence>
  - Notes: <only if genuinely non-obvious>
```

Notice how every part of Section 1–3 above shows up in this example: a short dash-separated `name`, a `description` with a clear "use when," a plain summary, and an explicit "do NOT use" — followed by a titled body with numbered steps and a defined output format.

---

## Final checklist before you save and use it

- [ ] `name` is short, lowercase, dash-separated, and describes the task
- [ ] `description` has all three parts: use-when, what-it-does, do-NOT-use-when
- [ ] You read the description out loud and it's unambiguous to a stranger
- [ ] The body has a clear title and a "When this applies" reminder
- [ ] Every step is a specific, imperative instruction — not a vague suggestion
- [ ] The exact output format is spelled out, not left to guesswork
- [ ] You tried the "before you start" phrasings mentally against the description and confirmed they'd trigger it — and that your Question 3 example correctly would NOT

**Where finished Skills usually live:** a folder named after your `name` field, containing a file called `SKILL.md`, e.g. `[project]/.claude/skills/[your-task-name]/SKILL.md`.
