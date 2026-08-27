# <Slug> — spec

**Created:** YYYY-MM-DD · **Status:** draft | decided | building | done | superseded
**Authority:** ssot for this slice · **Superseded by:** `<path>` (only when superseded)

> This file is the CONTRACT an `executor` builds to. Decided here, by the main session, BEFORE
> any agent is spawned; the executor's prompt points at this path instead of restating it.
> An executor never edits this file — a forced deviation is REGISTERED in its report and
> adjudicated by the integrator, who is the only writer here.

## Goal

One paragraph. What changes for the user or the system when this is done.

## Non-goals

What this slice deliberately does NOT do. Every line here is a redesign an executor is
forbidden to attempt.

## Acceptance — pre-registered

Written BEFORE building, or it is not acceptance. Each row must be checkable by someone who
did not build it.

| # | What will prove this worked | How it is checked |
|---|---|---|
| A1 | | command / walked path / query |
| A2 | | |

## Gates

The objective checks that must be green before the executor reports done — name the exact
commands, not their intent.

```bash
<typecheck>
<lint on touched files>
<the test suites this slice must not break>
```

## Slices

Ordered, independently mergeable. One executor per slice when they touch disjoint files;
sequential when they don't.

| # | Slice | Files it owns | Depends on |
|---|---|---|---|
| S1 | | | — |

## Inputs the executor is given

Paths it must read first (`CLAUDE.md`, the matching `.claude/rules/*.md`, the interfaces it
must not break), plus any fixture or account it may use.

## Open questions

Anything unresolved. **A spec with open questions blocking a slice is not `decided`** — resolve
it or move the slice out of this round.

## Registered deviations (filled at merge, by the integrator)

| # | What the executor hit | Why | Accepted / rejected |
|---|---|---|---|
