---
created: 2026-07-17
last-reviewed: 2026-07-17
---

# Doc governance — anti-drift

The enemy is DRIFT: a frozen doc that still looks current; the same fact restated in five
places, three of them stale. Same principle as the memory caps: thin active surface, one home
per fact, depth distilled out.

## Lifecycle frontmatter (every non-trivial doc)

| Field | Values |
|---|---|
| `status` | `current` · `frozen` · `superseded` · `planned` · `historical` · `archived` |
| `authority` | `ssot` (the one deciding home) · `derived` (a view; sources win) |
| `last_verified` | `YYYY-MM-DD` |
| `superseded_by` | a pointer (only when superseded) |

## The three rules

- **R1 — one SSOT per fact.** A derived doc POINTS at the value, never re-copies it. A
  derivable number (test count, LOC) is not restated as a live value at all — say "run the
  command"; historical mentions carry "(as of <date>)".
- **R2 — change a fact → grep for the old value** across all docs and fix/repoint EVERY hit in
  the SAME change. A stale copy that looks current is the #1 doc failure.
- **R3 — label, don't bury.** Superseded/historical docs keep their `status:` plus a one-line
  "replaced by" note. Archiving = `git mv` to an `archive/` dir + one manifest line
  (what/why/where-preserved). Out of the reading path, still greppable — never lost.

## Code change → same-commit doc updates

A load-bearing fact changed by a code change (a schema, a term's meaning, a model pin, a
state/status) updates its ONE ssot home in the SAME commit, followed by the R2 sweep.
