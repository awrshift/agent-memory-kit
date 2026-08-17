---
name: memory-audit
description: Audit MEMORY.md against the memory discipline — oversized sections, settled multi-session patterns that belong in knowledge/concepts/, stacked chronicle blocks, stale entries. Produces a move plan as a table for approval, then executes the approved moves atomically. Use when the SessionStart hook reports a tripped cap, when PreCompact blocks on an oversized cache, or when the user says "/memory-kit:memory-audit", "audit memory", "проверь память", "почисти память". Refuses only when no cap is tripped AND no settled-pattern candidate exists.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# Memory audit — the surgical one-file pass

This is the **cap-trip response**, not the daily ritual. `/memory-kit:close-session` runs every
session and captures; this runs when the hot cache has actually outgrown itself and something
must LEAVE it. Keeping them separate is the point: a daily ritual that also has to do surgery
becomes a ritual people skip.

**Always pause for approval before writing.** The user talks; you write — including here.

## Inputs

- `.claude/memory/MEMORY.md` — read in full.
- `knowledge/concepts/*.md` — filenames + first 5 lines, for duplicate detection (the directory
  may not exist yet; the first move creates it).
- `context/handoffs/` — to confirm a session narrative already lives there → **drop**, not move.

## Step 1 — classify every section

Scan by `## ` heading. For each, count lines and mark exactly one action:

| Mark | When |
|---|---|
| `move (create)` | a settled pattern (confirmed on 3+ distinct dates) with >25 lines of reference detail |
| `move (merge)` | same, but a concept article on the topic already exists |
| `drop` | a per-session chronicle — it already lives in a handoff; distil at most one settled line |
| `update in-place` | stale: names a deleted file, a closed ticket, a superseded decision |
| `simplify` | true and useful, but three times longer than it needs to be |
| `keep` | earns its lines |

## Step 2 — the move plan (a table, never prose)

| # | Section | Lines | Action | Target | Reason |
|---|---|---|---|---|---|
| 1 | … | N | move / merge / drop / simplify / keep | `knowledge/concepts/<slug>.md` or — | … |

Close the table with: estimated line savings, and the projected line/byte count afterwards
against the caps (180 lines / 32 KB / 3000 chars per line).

## Step 3 — PAUSE

Print the plan and ask for approval. Wait for an explicit yes or edits. No writes before that.

## Step 4 — execute the approved moves, atomically

- **move (create):** write `knowledge/concepts/<slug>.md` with frontmatter matching
  `knowledge/index.md`'s spec, then add its one-line entry to that index in the same pass.
- **move (merge):** append under a `### From MEMORY.md (YYYY-MM-DD)` header — never duplicate a
  section that already says the same thing.
- **in MEMORY.md:** replace the moved section with a one-line pointer plus a one-line teaser.
  A move without a pointer orphans the content — that is the failure this audit exists to prevent.
- **drop:** delete; keep at most one distilled line.

## Step 5 — the header, then the report

Replace the MEMORY.md current-state header (≤3 lines, dated). Report before/after line and byte
counts, every file touched, and save declined candidates to
`context/handoffs/memory-audit-deferred-YYYY-MM-DD.md` so the next audit starts from them.

## Refuse when

- No cap is tripped AND no settled-pattern candidate exists → say "no audit needed" and stop.
  A SINGLE tripped cap is reason enough to proceed (one 3000-char line qualifies).
- The user declines the plan → save it next to the handoffs and stop.

## Anti-patterns

- Writing anything before the approval.
- Creating a new concept when a keyword grep matches an existing one — merge bias broken.
- Promoting a session CHRONICLE into a knowledge article. Concepts hold settled patterns;
  narrative belongs to handoffs, and the action for it here is `drop`.
- Burying the plan in prose. The table is what makes it reviewable in ten seconds.
