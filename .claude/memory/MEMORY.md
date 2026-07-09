# Memory — Hot cache

**Current state:** fresh install — no work yet. (Agent: REPLACE these header lines at every
`/close-session` with 2-3 sentences of where things stand. This header is «current state»,
never a chronicle of past sessions — session detail lives in `context/handoffs/`.)

**Agent writes this file.** If you want to add a note, say it in conversation — the agent
captures and writes. Loaded on every session start.

---

## Why dates matter (load-bearing)

Every entry is `[YYYY-MM-DD]`-prefixed. This is what lets the `/close-session` audit work —
the agent greps for "this pattern across 3+ distinct dates" and proposes promotion to a rule
or concept. Without dates, every entry is timestamp-less noise. **An entry without a date tag
is a bug, not a stylistic choice.**

## Format

One line per entry, prefixed `[YYYY-MM-DD]`. Short. Scannable. No headings inside entries.

```
- [2026-04-24] user prefers plain prose for status updates, not dense tables
- [2026-04-23] for pricing tiers, highlighted plan must use scale-[1.02] + border-2 + badge (conversion +22%)
```

Group loosely by theme with empty lines if the file grows, but don't build a heavy hierarchy —
this is a hot cache, not a wiki.

---

## Entries

<!-- Agent appends date-tagged patterns here. When the same pattern is reinforced on 3+ dates,
the agent surfaces it at /close-session as a promotion candidate: knowledge/concepts/<topic>.md
(facts + rationale) or .claude/rules/<name>.md (mechanical constraint). Promoted entries get
pruned from here. -->

(empty — start talking; agent will begin capturing)

---

## What NOT to put here

- Session narratives (those live in `context/handoffs/<topic>-<date>.md`)
- Rationale essays longer than one line (those belong in `knowledge/concepts/*.md`)
- Mechanical always/never constraints (those promote to `.claude/rules/*.md`)
- Project-specific tasks (those live in `projects/<name>/BACKLOG.md`)
- Experiment progress notes (those live in `experiments/<name>-YYYYMMDD/EXPERIMENT.md`)

## The three caps (hook-enforced)

The SessionStart hook checks this file against **180 lines / 32 KB / 3000 chars per line** and
prompts an audit when any cap trips. Three caps because line count alone lies: content can
densify into ever-longer lines while `wc -l` stays flat. When a cap trips, `/close-session`
promotes settled patterns out and prunes absorbed ones.
