<!-- memory-kit protocol v6.5.4 — managed block; a newer kit version REPLACES everything down to the end marker -->
# Memory protocol (for any agent working in this repository)

This repository keeps agent memory in plain files. Follow this protocol every session.
(Hosts that run the `memory-kit` plugin's hooks — Claude Code — enforce it automatically;
there, prefer the plugin's skills over doing this by hand.)

## At session start — read first

1. `.claude/memory/MEMORY.md` — durable patterns + current state (the hot cache).
2. The newest file in `context/handoffs/` — where the last session left off.
3. `knowledge/index.md` — catalog of deep memory; open articles only when needed.

## Two invariants

- **The user talks, the agent writes.** Propose in conversation, get a yes, write the
  file, say what you wrote.
- **Every memory entry starts with a `[YYYY-MM-DD]` date tag.** An undated entry is a bug.
  A stored fact about the OUTSIDE world older than ~7 days is a hypothesis — re-check first.

## Caps on MEMORY.md

A hot cache, not an archive: **180 lines / 32 KB / 3000 chars per line**. Cap tripped →
audit before other work: promote patterns seen on 3+ distinct dates into
`knowledge/concepts/<topic>.md` (ask first), prune what you promote. One home per fact —
when a fact changes, fix its restatements in the same pass.

## Before context compaction / when context runs long

Save state FIRST: dated entries into MEMORY.md plus a fresh 2–3 sentence current-state
header. Compacting on a stale cache silently loses the session.

## Tests

A failing test means the CODE is wrong, not the test. Do not edit an existing test you did
not create this session without asking the user.

## At session close

1. Capture today's durable observations as dated lines in MEMORY.md.
2. A pattern on 3+ distinct dates is a promotion CANDIDATE — propose, ask.
3. REPLACE the MEMORY.md header with current state (2–3 sentences; never stack history).
4. Write `context/handoffs/<topic>-YYYY-MM-DD.md`: done · open · next · where things live.
<!-- /memory-kit protocol -->
