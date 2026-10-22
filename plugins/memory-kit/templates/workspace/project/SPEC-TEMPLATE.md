# <Slug> — spec

**Created:** YYYY-MM-DD · **Status:** draft | decided | building | done | superseded | assumed | stale
**Authority:** ssot for this slice · **Superseded by:** `<path>` (only when superseded)
**Depth pass:** YYYY-MM-DD · <what the pass changed, or «nothing changed because …»>
**Practice:** <dated research file with sources> | not needed because <…>
**Review:** <high | medium | low> · <why> · <who>
(What each of these three lines owes, and why: the plugin's `reference/spec-depth.md`. No depth-pass line → an
executor does not start.)

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
did not build it. The ids are stable: executor slices, qa runs, tests and the findings registry
reference them by name. `Verified` is filled by the integrator only — a date plus a pointer to
the run record or the gate output. Judge the OUTCOME the user gets; a counter, a gate pass or a
model judge's score is «screen only», never the proof.

| # | What will prove this worked | How it is checked | Verified |
|---|---|---|---|
| AC-1 | | command / walked path / query | |
| AC-2 | | | |

## Value sources

List every value this slice must produce, compute or display. Each source is an input, a store
column, a derivation from a named value, or a prior decision (spec id). **A value with no source
is an OWED DECISION and this spec is not `decided`.**

| Value | Source |
|---|---|
| | |

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

| # | Slice | Files it owns | Serves | Depends on |
|---|---|---|---|---|
| S1 | | | AC-1, AC-2 | — |

## Inputs the executor is given

Paths it must read first (`CLAUDE.md`, the matching `.claude/rules/*.md`, the interfaces it
must not break), plus any fixture or account it may use.

## Failure branches — written before the build

Per failure mode: what is tried next, and whose call it is (a redesign inside the approach = the agent; a change to
what the user gets = the user). Cover the mixed outcome too. The bar above is not moved after the results are seen.

| If … | Then … | Whose call |
|---|---|---|
| | | |

## Open questions

Anything unresolved. **A spec with open questions blocking a slice is not `decided`** — resolve
it or move the slice out of this round.

## Registered deviations (filled at merge, by the integrator)

| # | What the executor hit | Why | Accepted / rejected |
|---|---|---|---|
