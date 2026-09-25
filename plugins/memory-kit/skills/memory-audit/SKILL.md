---
name: memory-audit
description: Audit MEMORY.md against the memory discipline — oversized sections, settled multi-session patterns that belong in knowledge/concepts/, session-headed chronicle blocks, restated rules, copied numbers, stale entries. Produces a move plan as a table for approval, then executes the approved moves atomically. Use when the SessionStart hook reports a tripped cap or session-headed blocks, when PreCompact blocks on an oversized cache, or when the user says "/memory-kit:memory-audit", "audit memory", "проверь память", "почисти память". Refuses only when no cap is tripped, no session block is flagged AND no settled-pattern candidate exists.
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
- The newest `context/audits/memory-audit-deferred-*.md`, if one exists — the candidates the
  previous audit left; start from them.

## Step 1 — classify every section

Scan by `## ` heading (and `###` inside a long section). For each, count lines and mark exactly
one action. Also read the project's `CLAUDE.md`, the `.claude/rules/*.md` without `paths:` and
the plugin's `reference/` titles — you need them for `restates-rule`.

| Mark | When |
|---|---|
| `move (create)` | a settled pattern (confirmed on 3+ distinct dates) with >25 lines of reference detail |
| `move (merge)` | same, but a concept article on the topic already exists |
| `session-block` | the heading names a session or a date, not a topic (`### s66 (2026-09-25)`, `## Session 65 wrap`, `## Findings [date] — …`; the SessionStart hook flags these) → dissolve by topic: each settled lesson → one line under its topic heading or a concept; the rest → drop |
| `drop` | a per-session chronicle — it already lives in a handoff; distil at most one settled line |
| `restates-rule` | the entry says what `CLAUDE.md`, an always-loaded rule or a `reference/` file already says → drop, or one pointer line if the link is not obvious. The agent reads those files every session; a second copy only drifts |
| `point to SSOT` | a derivable number — price, count, version, limit — whose source of truth lives elsewhere (a price table in code, a config, a vendor page) → replace the value with a pointer to that source (`reference/doc-governance.md` R1). A copied number outlives the thing it described |
| `update in-place` | stale: names a deleted file, a closed ticket, a superseded decision |
| `simplify` | true and useful, but three times longer than it needs to be |
| `keep` | earns its lines |

## Step 2 — the move plan (a table, never prose)

| # | Section | Lines | Action | Target | Reason |
|---|---|---|---|---|---|
| 1 | … | N | move / merge / session-block / drop / restates-rule / point to SSOT / simplify / keep | `knowledge/concepts/<slug>.md` or — | … |

Close the table with: estimated line savings, and the projected line/byte count afterwards
against the caps (180 lines / 32 KB / 3000 chars per line). **Target well below the caps — at
most ~60 % of the byte cap (≈ 20 KB).** A cache audited to «just under» refills past the cap
within days: the cap works as a fill line, not a ceiling. If the plan does not reach the target,
say which sections keep it above and why they earn their bytes.

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
- **session-block:** put each surviving lesson under its topic heading (create the topic heading
  if none fits), then delete the session heading and the rest of its block.
- **restates-rule / point to SSOT:** delete the copy; where a reader would not find the source
  unaided, leave one line naming the file (and the symbol or section) that holds it.

## Step 5 — the header, then the report

Replace the MEMORY.md current-state header (≤3 lines, dated). Report before/after line and byte
counts, every file touched, and save declined candidates to
`context/audits/memory-audit-deferred-YYYY-MM-DD.md` (create the dir if absent) so the next audit
starts from them. Not in `context/handoffs/`: the SessionStart hook injects the newest file there
as the session handoff, so a deferred list saved there replaces the real handoff at the next start.

## Refuse when

- No cap is tripped, no session-headed block is flagged AND no settled-pattern candidate exists →
  say "no audit needed" and stop. A SINGLE tripped cap or flagged block is reason enough to
  proceed (one 3000-char line qualifies).
- The user declines the plan → save it to `context/audits/` as above and stop.

## Anti-patterns

- Writing anything before the approval.
- Creating a new concept when a keyword grep matches an existing one — merge bias broken.
- Promoting a session CHRONICLE into a knowledge article. Concepts hold settled patterns;
  narrative belongs to handoffs, and the action for it here is `drop`.
- Stopping at «just under the cap». The next few sessions refill it; aim for the ~60 % target.
- Keeping a rule «as a reminder». If the always-loaded layer already says it, memory repeating
  it is how two versions of one rule start to disagree.
- Burying the plan in prose. The table is what makes it reviewable in ten seconds.
