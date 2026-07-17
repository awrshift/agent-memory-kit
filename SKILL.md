---
name: claude-memory-kit
description: "Persistent memory for Claude Code agents with an agent-audit-ritual architecture. User only talks; the agent captures, audits, proposes promotions, and writes. Memory lives in layers — a hot cache (MEMORY.md) held under three size caps, per-session handoffs (context/handoffs/), topical knowledge articles (knowledge/concepts/), and canonical rules (.claude/rules/) — plus multi-project isolation via projects/<name>/ and an experiments/ sandbox. /close-session runs the end-of-session audit ritual. Zero external dependencies."
tags: [memory, context-management, productivity, claude-code, agent-memory, knowledge-base, multi-project]
version: 5.1.0
author: awrshift
license: MIT
repository: https://github.com/awrshift/claude-memory-kit
---

# Claude Memory Kit v5

Persistent memory for Claude Code agents. Layered memory, agent-driven promotion, zero manual file editing. The v5 **lean core**: two operators, per-session handoffs, memory that fails loudly instead of rotting quietly.

## Two core invariants

1. **User only talks. Agent captures, proposes, writes.** Every architectural decision passes this test.
2. **Every memory entry carries a `[YYYY-MM-DD]` date tag.** This is what lets `/close-session` detect cross-session repetition and propose promotions.

## What's new in v5

- **Session close is `/close-session`, not `/close-day`.** The ritual: capture dated patterns → audit for 3+-date repetition → promote on your "yes" → replace the MEMORY.md header (current state, never a chronicle) → write a per-session handoff.
- **Per-session handoffs replace the rolling next-session-prompt.** One immutable note per closed session in `context/handoffs/<topic>-YYYY-MM-DD.md`; the SessionStart hook injects the newest one. No rolling file to freeze while looking authoritative.
- **Three independent MEMORY.md caps, hook-enforced: 180 lines / 32 KB / 3000 chars per line.** Line count alone lies — content densifies into ever-longer lines while `wc -l` stays flat. Any tripped cap opens the next session with an audit prompt.
- **Stale-reference detector.** Every session start, file paths mentioned in memory are checked against disk; anything moved or missing is flagged.
- **The daily journal (`daily/` + `/close-day`) moved to opt-in `.kit/advanced/close-day-layer/`** — it was the layer that silently rotted in long-running use. One `cp` re-enables it.

See [.kit/CHANGELOG.md](.kit/CHANGELOG.md) for full migration notes.

## Quick start

```bash
git clone https://github.com/awrshift/claude-memory-kit.git my-project
cd my-project
claude
```

First session: agent greets you, asks 2-3 setup questions, loads you in. Type `/tour` for a guided walkthrough.

## Daily workflow

1. Open a session — the hook auto-loads the newest handoff + MEMORY health stats + knowledge index
2. Work normally — agent captures patterns in MEMORY.md as you speak
3. `/close-session` when done — agent audits for promotions, proposes verbally, writes on your verbal "yes", and leaves the handoff note for next time

Tomorrow starts where today left off — from that handoff.

## Included skills

Default — the whole loop:

| Skill | Description |
|---|---|
| `/close-session` | End-of-session audit ritual: capture + promotion proposals + MEMORY header refresh + handoff |
| `/tour` | Interactive guided walkthrough on your own files |

Opt-in (`.kit/advanced/`, copy into `.claude/` to enable):

| Skill | Description |
|---|---|
| `/close-day` | Day-by-day journal layer (`close-day-layer/`) — synthesizes a daily log, backfills missed days from git history |
| `/memory-usage` | Read-only telemetry: hot files vs cold archival candidates |
| `/memory-lint` | Structural hygiene (broken links, sparse articles, orphans) |
| `/session-review` | Orchestration layer — end-of-session adversarial review with independent reviewers |
| `/second-opinion` | Orchestration layer — cross-check a high-stakes answer (Devil's Advocate · Boardroom · Round-Table) |

The orchestration layer (`.kit/advanced/orchestration-layer/`) also ships three agents —
`executor` (builds to a decided spec in a worktree), `recon` (read-only fact-gatherer),
`idea-validator` (isolated adversarial critic) — and four rules (orchestrator fact-check ·
parallel development · doc governance · decisions log) for multi-agent development.

## Architecture

Memory lives in layers, each answering a different question:

| Layer | Answers | Written by |
|---|---|---|
| `.claude/memory/MEMORY.md` | «what patterns repeat» + «where things stand» | agent as you speak |
| `context/handoffs/*.md` | «what happened, session by session» | agent via `/close-session` |
| `knowledge/concepts/*.md` | «facts and rationale by topic» | agent after your "yes" on `/close-session` |
| `.claude/rules/*.md` | «what must always / never happen» | agent after a long-stable pattern |

Promotion runs observation → candidate → law: a dated pattern in `MEMORY.md` that repeats on 3+ distinct dates becomes a `knowledge/concepts/` article or a `.claude/rules/` constraint on `/close-session` — always agent-written, always on your verbal confirmation.

See [.kit/ARCHITECTURE.md](.kit/ARCHITECTURE.md) for full details and [CLAUDE.md](CLAUDE.md) for the agent's session workflow.

## Built from production use

Iteration on 800+ real sessions across 8+ projects. Every component earns its place; `experiences/`, background-detection scripts, generic role-guidance seeds — and, in v5, the daily-chronicle default — didn't survive review.
