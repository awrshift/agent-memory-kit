---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# Reporting to the user — progress in their units, comments before decisions, plans in rounds

> Read on demand, before a status message, a session-close report, or an answer to the user's comment. What the user
> alone decides is in `templates/rules/orchestration.md` item 9; how a claim in a message is checked is in
> `orchestrator-fact-check.md`. This file is about how the message reads.

**Applies when:** the user reads your messages without having watched the work, or reacts to it with comments.

## 1. Lead with the outcome, in the user's words

Open with the outcome in one plain sentence, then what you need from the user. The labels you work with — decision and
finding ids, session numbers, rule ids, family slugs, branch and file names — are yours, not theirs: drop them, or
give each its own plain clause. Full sentences: no arrow chains, slash-packed lists or stacked parentheses; gloss a
technical term the first time it appears. When short and clear pull apart, choose clear.
(one project's working practice; no count)

## 2. Progress in the user's own units

When the user follows progress on some page or gauge of their own (a stage and its level, fields built of all,
tasks done of the stage), every report speaks in THOSE units, plus one plain sentence of what the product can now do:

- **At session start** — per item the session aims to move: «now → target», and why this order. An item with no move
  for two or more days is named without being asked.
- **When a piece of work is accepted** — before → after in those units, or «it did not move on the page, because …»;
  «works only together with X» when one piece needs another.
- **At the close** — a before → after table per item, the share of the session's plan done, and «nothing moved this
  session» said plainly when that is true.
- **Numbers come from the script or snapshot that feeds the page**, never from memory.

Why: the user had said they lacked any sense of whether the work was moving at all, or in the right direction.
(one project's working practice; no count)

## 3. A comment is not a decision

A comment from the user on a page, a plan or a result is INPUT. Before changing anything, answer in three parts —
**how it works now · what I take from the comment · what I did not understand** — and write the change after the
user's answer. An architecture question that surfaces inside another task is not decided in passing: it becomes its
own piece of work, with the field's practice checked first (`spec-depth.md` §2).
(one project's working practice; no count)

## 4. Questions the user gets

- Decisions that are the user's (product, money, external actions) go as a short questionnaire: options and your
  recommendation. Technical choices inside the agreed scope are reported, not asked.
- **Before asking, re-read what is already decided.** In one project, three of four «product questions» prepared for
  the user had already been decided in an earlier design.
  (measured in one project, 2026-10: 3 of 4 prepared questions already decided)
- When you recommend a cheap patch instead of the foundation, say so in those words — patch, and what the foundation
  would be (`review-loop.md` §0).
  (one project's working practice; no count)
- Times in a message in the user's own time zone; in documents, UTC.
  (one project's working practice; no count)

## 5. A plan is counted in rounds and dependencies, not calendar days

Agent work does not follow the calendar: a day can hold many sessions. Name a term as a
number of rounds (build, review, fix) and what the next step waits on — a review, a measurement, the user's answer —
never «tomorrow» or «the day after» without a reason that is itself a date (someone else's schedule, a release).
(one project's working practice; no count)

Related: `window-cycle.md` (where reports from parallel windows go) · `doc-governance.md` R1 (who keeps the order of
work).
