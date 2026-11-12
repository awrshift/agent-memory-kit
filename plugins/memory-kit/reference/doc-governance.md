---
created: 2026-07-17
last-reviewed: 2026-11-12
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
| `status` | `current` · `frozen` (optional; absent = `current`). The ONE status vocabulary of the kit — `knowledge/concepts/` articles use it too. A doc that would be superseded, historical or archived is deleted instead (R3) |
| `authority` | `ssot` (the one deciding home) · `derived` (a view; sources win) (optional) |

## The rules

- **R1 — one SSOT per fact.** A derived doc POINTS at the value, never re-copies it. A
  derivable number (test count, LOC, an open-PR count) is not restated as a live value at all — say "run the
  command"; a dated record (a report, a handoff) states it "(as of <date>)".
  *Applies when more than one document tracks progress or the order of work:* state that code or git can derive (a
  status a script computes, a task's «done» that its commit shows) is not kept by hand at all; what is kept by hand
  is judgement — a decision, a ruling, its why — written at the event (the acceptance of a piece of work), not
  reconstructed at the session close. The order of work has ONE home (a file or script that says what waits on
  what), and it is checked against the decisions, not against other files: work ahead of that order runs only with
  a written decision and a date (one project's working practice; no count).
- **R2 — change a fact → grep for the old value** across all docs and fix/repoint EVERY hit in
  the SAME change. A stale copy that looks current is the #1 doc failure.
- **R3 — current state only; the past lives in git.** A doc holds what work needs now: a stale line is deleted the
  moment it is seen (no «was X», no `## History`, no «replaced by» stub), and a whole doc no work needs is deleted with
  its live references fixed in the SAME change — `git log -S` finds the past. A dated record (a report, an acceptance,
  a handoff) is not edited after the fact; it is deleted when nothing live cites it.
  *Applies when you delete, move or reorganise more than a handful of files:* the change rewrites every live
  reference in the SAME change (a script that moves or deletes and rewrites, with a broken-reference count against a
  baseline), and its gate runs every consumer a link check cannot see — code that builds the path at run time, and builders that parse the
  moved or rewritten file's structure (a page generated from a status file's headings). A file a script builds a path
  to stays put until that script's data is next revised (measured in one project, 2026-11: two batches moved 753 and
  10,739 files and rewrote 101 and 430 live files with 0 new broken references; the consumer gate was added after a
  page builder failed — a module it imported had been archived, and the status file it parsed had lost its section).
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
