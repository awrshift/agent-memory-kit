---
created: 2026-07-17
last-reviewed: 2026-10-22
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
| `status` | `current` · `frozen` · `superseded` · `historical` · `archived` (optional; absent = `current`). The ONE status vocabulary of the kit — `knowledge/concepts/` articles use it too |
| `authority` | `ssot` (the one deciding home) · `derived` (a view; sources win) (optional) |
| `superseded_by` | a pointer (only when superseded) |

## The rules

- **R1 — one SSOT per fact.** A derived doc POINTS at the value, never re-copies it. A
  derivable number (test count, LOC, an open-PR count) is not restated as a live value at all — say "run the
  command"; historical mentions carry "(as of <date>)".
- **R2 — change a fact → grep for the old value** across all docs and fix/repoint EVERY hit in
  the SAME change. A stale copy that looks current is the #1 doc failure.
- **R3 — label, don't bury.** Superseded/historical docs keep their `status:` plus a one-line
  "replaced by" note. Archiving = `git mv` to an `archive/` dir + one manifest line
  (what/why/where-preserved). Out of the reading path, still greppable — never lost.
- **R4 — no symlinks to other repositories.** They die silently when the other repo moves. Reference by path, or copy
  with a provenance line when this repo owns the copy.
- **R5 — nothing a doc cites lives only in a session scratchpad.** The scratchpad (`/tmp`, a session temp dir) dies with
  the session. A script, an output, a draft or a data file that a doc, plan or PR text relies on is copied into the
  repository in the SAME change and cited there. Secrets never move. A reference that cannot be recovered is marked «lost».
- **R6 — a decision is either built or says why not.** Every decisions-log entry that needs a build carries a build-by
  date or a dated «not built — why / replaced by» line; a status rewrite re-reads the open ones. Code that ships a new
  signal (a column, a flag, a score) names who reads it — a signal nothing consumes is a report, not a gate.

## External state expires

A fact about the outside world — an open PR, «the client is waiting», a price, a model id, a vendor's API behaviour —
older than ~7 days is a HYPOTHESIS: re-check it live before acting. A practice or standard («how the industry does X»)
is re-checked after ~30 days when it steers a design.

## Code change → same-commit doc updates

A load-bearing fact changed by a code change (a schema, a term's meaning, a model pin, a
state/status) updates its ONE ssot home in the SAME commit, followed by the R2 sweep.
