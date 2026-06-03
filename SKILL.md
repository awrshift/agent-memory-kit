---
name: claude-memory-kit
description: "Persistent memory for Claude Code agents with an agent-audit-ritual architecture. User only talks; the agent captures, audits, proposes promotions, and writes. Memory lives in layers — daily logs, hot cache (MEMORY.md), topical knowledge articles (knowledge/concepts/), and canonical rules (.claude/rules/) — plus multi-project isolation via projects/<name>/ and an experiments/ sandbox. /close-day runs the end-of-day audit ritual. Zero external dependencies."
tags: [memory, context-management, productivity, claude-code, agent-memory, knowledge-base, multi-project]
version: 4.1.3
author: awrshift
license: MIT
repository: https://github.com/awrshift/claude-memory-kit
---

# Claude Memory Kit v4

Persistent memory for Claude Code agents. Layered memory, agent-driven promotion, zero manual file editing.

## Two core invariants

1. **User only talks. Agent captures, proposes, writes.** Every architectural decision passes this test.
2. **Every memory entry carries a `[YYYY-MM-DD]` date tag.** This is what lets `/close-day` detect cross-session repetition and propose promotions.

## What's different from v3.2

- **Agent-driven promotion ritual** via `/close-day` (was: background `promote-patterns.py` detection + `flush.py` auto-flush, both killed as unreliable and invariant-violating)
- **Multi-project isolation** via `projects/<name>/` — shared layers load always, per-project scope on demand
- **`experiments/<name>-YYYYMMDD/`** sandbox layer next to `projects/` — different lifecycle, no direct promotion to rules
- **Date-tagging promoted to a documented load-bearing invariant** (was implicit machinery, now stated)
- **Killed:** `experiences/` staging layer, `promote-patterns.py` + `flush.py` background scripts, `playbooks/` and `<role>-guidance/` reference-skill seeds, the `/memory-audit` and `/memory-compile` operators, and the `knowledge/connections/` + `knowledge/meetings/` subdirs. The role-guidance pattern still works if you add it per-project (see `.kit/ARCHITECTURE.md` § "Adding role-guidance yourself"); the kit just doesn't ship templates.
- **Default surface trimmed to two operators** (`/close-day` + `/tour`). The wiki-maintenance commands (`/memory-lint`, `/memory-query`) plus a usage-telemetry tool (`/memory-usage`) moved to opt-in `.kit/advanced/` — see its README to enable.

See [.kit/CHANGELOG.md](.kit/CHANGELOG.md) for full migration notes.

## Quick start

```bash
git clone https://github.com/awrshift/claude-memory-kit.git my-project
cd my-project
claude
```

First session: agent greets you, asks 2-3 setup questions, loads you in. Type `/tour` for a guided walkthrough.

## Daily workflow

1. Open a session — hooks auto-load NSP + MEMORY + knowledge index
2. Work normally — agent captures patterns in MEMORY.md as you speak
3. `/close-day` when done — agent synthesizes today, audits for promotions, proposes verbally, writes on your verbal "yes"

Tomorrow starts where today left off.

## Included skills

Default — the whole daily loop:

| Skill | Description |
|---|---|
| `/close-day` | End-of-day audit ritual: synthesis + promotion proposals. Auto-backfills missed working days from git history. |
| `/tour` | Interactive guided walkthrough on your own files |

Opt-in (`.kit/advanced/`, copy into `.claude/` to enable):

| Skill | Description |
|---|---|
| `/memory-usage` | Read-only telemetry: hot files vs cold archival candidates |
| `/memory-lint` | Structural hygiene (broken links, sparse articles, orphans) |
| `/memory-query` | Natural-language search across the knowledge base |

## Architecture

Memory lives in layers, each answering a different question:

| Layer | Answers | Written by |
|---|---|---|
| `daily/YYYY-MM-DD.md` | «what happened today» | agent via `/close-day` |
| `.claude/memory/MEMORY.md` | «what patterns repeat across sessions» | agent as you speak |
| `knowledge/concepts/*.md` | «facts and rationale by topic» | agent after your "yes" on `/close-day` |
| `.claude/rules/*.md` | «what must always / never happen» | agent after a long-stable pattern |

Promotion runs liquid → amber → crystal: an observation in `daily/` becomes a date-tagged pattern in `MEMORY.md`, which `/close-day` may promote to a `knowledge/concepts/` article or a `.claude/rules/` constraint — always agent-written, always on your verbal confirmation.

See [.kit/ARCHITECTURE.md](.kit/ARCHITECTURE.md) for full details and [CLAUDE.md](CLAUDE.md) for the agent's session workflow.

## Built from production use

Iteration on 700+ real sessions across 7+ projects. Every component earns its place; `experiences/`, background-detection scripts, and generic role-guidance seeds didn't survive review.
