---
name: close-session
description: End-of-session ritual — audit today's patterns against accumulated memory, propose promotions, refresh MEMORY.md, and write the session handoff. Use when the user says "/memory-kit:close-session", "закрой сессию", "закрываем", "we're done for today", "wrap up".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# /close-session — the end-of-session ritual

You close the session in four steps. Don't just dump — **audit**. Everything you write, you
announce briefly; anything promoted to rules/concepts needs the user's verbal "yes" first.

## Step 1 — Capture what's new
Scan this session for observations worth keeping. Append each to `.claude/memory/MEMORY.md`
as a ONE-LINE `[YYYY-MM-DD]`-prefixed entry. Short, scannable, no essays (long rationale
belongs in a concept article, step 2).

## Step 2 — Audit & promote (the valuable part)
Read the date-tagged entries in MEMORY.md. Look for repetition: **did this pattern appear on
3+ different dates?** Surface 2-4 candidates, be specific: "noticed [date], [date], [date] you
said X — codify as a rule or a concept article?"
- User says yes → write `knowledge/concepts/<topic>.md` (facts + rationale; frontmatter per
  `knowledge/index.md` spec) or `.claude/rules/<name>.md` (mechanical always/never constraint;
  only for patterns stable 6+ months). Update `knowledge/index.md` (one line per concept).
- Promoted or long-absorbed entries get PRUNED from MEMORY.md — that's how it stays under its
  caps (180 lines / 32 KB / 3000 chars per line).
- Writing a fact into a second place? `reference/doc-governance.md` — one SSOT per fact, and when
  a fact changes you grep its restatements in the same pass. A product or architecture decision
  goes to the ledger instead — `projects/<name>/decisions-log.md`, format in
  `reference/decisions-log.md`. A plan, a spec, a research finding or a QA record is NOT memory:
  it belongs in that project's folder, per the map in its `README.md`.

## Step 3 — Refresh the MEMORY.md header
The header (everything above the first `---`) is «current state of work», 2-3 sentences,
**REPLACED** every close — never a chronicle of past sessions. Per-session detail lives in the
handoff, not stacked in the header.

## Step 4 — Write the handoff
Copy `context/handoffs/HANDOFF-TEMPLATE.md` → `context/handoffs/<topic>-<YYYY-MM-DD>.md` and
fill its five sections (what was done · where things stand · memory updates · next steps ·
opening note). The SessionStart hook injects the newest handoff next time — this file IS the
"remember where we left off" mechanism.

## Also check (30 seconds)
- **Experiment hygiene:** any `experiments/*-YYYYMMDD/` older than 30 days → ask: still active
  or close (distill → delete)?
- **Backlogs:** `projects/*/BACKLOG.md` task statuses reflect today's reality — a `DONE`
  nobody verified is still `IN PROGRESS`.
- **Project map:** anything you wrote today into a project folder is a row in that project's
  `README.md` map, and the map's `Last verified` is today's date.
- **Caps:** if MEMORY.md is near any cap, do a deeper prune now, not "next time".

## What NOT to do
- Don't promote without the user's yes. Repetition makes a CANDIDATE, not a rule.
- Don't stack "Prior session" paragraphs in the MEMORY header — replace it.
- Don't write a handoff longer than ~1 screen. It's a note, not a transcript.
