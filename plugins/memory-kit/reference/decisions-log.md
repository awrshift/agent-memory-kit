---
created: 2026-07-17
last-reviewed: 2026-07-17
---

# Decisions log — a lean grep-by-id ledger

Keep ONE append-only file **per project** — `projects/<name>/decisions-log.md` — recording WHAT
was decided, one numbered entry per decision (`D-001`, `D-002`, …). Depth lives in its deep home;
the ledger stays lean enough to grep. One ledger per project, never one shared ledger with five
clients interleaved: the ids would collide and the grep would lie. If this repository already
keeps its ledger elsewhere, leave it there and repoint the row in `projects/<name>/README.md`.

## Shape

- **An index table** of every decision: `id | one-line summary | deep home | date`.
- **Full entries** for the current phase only, each ≤ ~4 lines: the decision + a one-phrase
  why + a pointer to the deep home.
- **What earns an entry:** a product or architecture decision. Reviews, doc scaffolds, process
  tweaks → the session handoff instead.

## Deep homes (never duplicate into the ledger)

| Content | Home |
|---|---|
| why + alternatives of an architectural decision | the spec that carries it, `projects/<name>/plans/` |
| a settled multi-session lesson | `knowledge/concepts/` |
| raw session detail | `context/handoffs/` |

## Discipline

- Append-only in spirit: entries are relocated (to an archive file, in id order), never
  rewritten. An entry that turned out wrong gets a dated correction line, not an edit.
- On a soft cap (~250 lines): move the oldest settled phase's full entries to the archive
  file — but FIRST confirm each entry's depth exists in its deep home; keep the index rows.
- Never archived: the format rule, the full index table, current-phase entries.
