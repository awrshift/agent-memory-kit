# Advanced add-ons (opt-in)

The default kit is deliberately tiny: `/close-session` (the end-of-session audit ritual) and `/tour` cover the whole loop for most people. Everything in this folder is **opt-in** — the day-by-day journal layer, plus power-user tooling for maintaining a knowledge base once it has grown.

> Unlike the rest of `.kit/` (which is pure documentation, safe to delete), this subfolder contains *functional* scripts, skills, and commands. They do nothing until you enable them.

## What's here

| Add-on | Where | What it does | Cost |
|---|---|---|---|
| **Orchestration layer** | `orchestration-layer/` → see its [README](orchestration-layer/README.md) | Multi-agent working mode for building things: executor + recon + idea-validator agents, `/session-review` + `/second-opinion` skills, and the fact-check / parallel-development / doc-governance / decisions-log rules. | Free (subagent tokens) |
| Daily-chronicle layer (`/close-day`) | `close-day-layer/` → see its [README](close-day-layer/README.md) | The v4 per-day journal (`daily/YYYY-MM-DD.md`) + the `/close-day` ritual (synthesis, git-history backfill of missed days) + the retired NSP template. Composes with the v5 core: `/close-day` writes the diary, `/close-session` still owns the audit + handoff. | Free, no LLM |
| `/memory-usage` | `aggregate_usage.py` + `usage_config.py` | Reads your session transcripts and reports **hot files** (used a lot) vs **cold candidates** (0 reads in 30 days → safe to archive). Turns "what can I prune?" into data. | Free, read-only |
| `/memory-lint` | `lint.py` | 5 structural health checks on `knowledge/` (broken `[[wikilinks]]`, orphan pages, missing backlinks, sparse articles, missing frontmatter). | Free, no LLM |

## Why these aren't in the default kit

- **The daily-chronicle layer** (`/close-day` + `daily/`) was a v4 *default*; v5 demoted it because in long-running use it was the part that silently rotted — days went unclosed, and the rolling next-session-prompt froze while still looking authoritative. The v5 core replaces it with per-session handoffs (which can't go stale unnoticed). Keep the journal only if you genuinely want a day-by-day work diary.
- **`/memory-usage`** is the most valuable of the three commands, but its signal is thin until you have weeks of sessions and a real knowledge base — so it's an add-on, not a day-1 default.
- **`/memory-lint`** is wiki-gardening (broken links, backlinks). Useful for a large hand-linked base; noise for a casual user.
- **The orchestration layer** is for people who BUILD with subagents (software, agent systems). Its invariants add process weight a memory-only user doesn't need.

Removed entirely over the versions: `/memory-compile` (auto-folding daily logs was unreliable — the audit ritual writes `knowledge/concepts/` directly, on your verbal "yes") and `/memory-query` (v5.1 — it never earned its subprocess: just ask the agent "what do we know about X?" in conversation and it reads the index + concepts directly).

## How to enable

**The orchestration layer** and **the daily-chronicle layer** each have their own one-`cp` enable step — see [`orchestration-layer/README.md`](orchestration-layer/README.md) and [`close-day-layer/README.md`](close-day-layer/README.md).

For the two power-user commands, copy them and their scripts into the live `.claude/` tree, then restart Claude Code:

```bash
mkdir -p .claude/memory/scripts
cp .kit/advanced/scripts/*.py   .claude/memory/scripts/
cp .kit/advanced/commands/*.md  .claude/commands/
```

That's it — `/memory-usage` and `/memory-lint` are now live slash commands. To disable, delete the copies from `.claude/`.

> Note the format difference: the core operators are **skills** (`.claude/skills/<name>/SKILL.md`), while these two are **commands** (`.claude/commands/<name>.md`) — a thin wrapper whose `## Execution` line runs the script. Both are native Claude Code mechanisms; commands fit script-runners best.

Enable only the ones you want: copy a single command's `.md` plus the script it names in its `## Execution` line (and `config.py` for `/memory-lint`, which imports it).
