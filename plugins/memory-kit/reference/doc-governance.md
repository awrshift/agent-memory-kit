---
created: 2026-07-17
last-reviewed: 2026-07-17
---

# Doc governance — anti-drift

The enemy is DRIFT: a frozen doc that still looks current; the same fact restated in five
places, three of them stale. Same principle as the memory caps: thin active surface, one home
per fact, depth distilled out.

## Lifecycle frontmatter (every non-trivial doc)

The minimum is two dates — the same pair the kit's own `reference/` docs and rule template
carry. The rest is opt-in for repositories whose docs actually change status.

| Field | Values |
|---|---|
| `created` | `YYYY-MM-DD` — required |
| `last-reviewed` | `YYYY-MM-DD` — required; bump it when you re-verify, not when you edit |
| `status` | `current` · `frozen` · `superseded` · `planned` · `historical` · `archived` (optional; absent = `current`) |
| `authority` | `ssot` (the one deciding home) · `derived` (a view; sources win) (optional) |
| `superseded_by` | a pointer (only when superseded) |

`knowledge/concepts/` articles use the richer schema in `knowledge/index.md` (title · status ·
created · updated · tags) — that index is their SSOT, not this table.

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
