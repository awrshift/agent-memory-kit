# Advanced add-ons (opt-in)

The default kit is deliberately tiny: `/close-session` (the end-of-session audit ritual) and `/tour` cover the whole loop for most people. Everything in this folder is **opt-in** — the day-by-day journal layer, plus power-user tooling for maintaining a knowledge base once it has grown.

> Unlike the rest of `.kit/` (which is pure documentation, safe to delete), this subfolder contains *functional* scripts, skills, and commands. They do nothing until you enable them.

## What's here

| Add-on | Where | What it does | Cost |
|---|---|---|---|
| Daily-chronicle layer (`/close-day`) | `close-day-layer/` → see its [README](close-day-layer/README.md) | The v4 per-day journal (`daily/YYYY-MM-DD.md`) + the `/close-day` ritual (synthesis, git-history backfill of missed days) + the retired NSP template. Composes with the v5 core: `/close-day` writes the diary, `/close-session` still owns the audit + handoff. | Free, no LLM |
| `/memory-usage` | `aggregate_usage.py` + `usage_config.py` | Reads your session transcripts and reports **hot files** (used a lot) vs **cold candidates** (0 reads in 30 days → safe to archive). Turns "what can I prune?" into data. | Free, read-only |
| `/memory-lint` | `lint.py` | 5 structural health checks on `knowledge/` (broken `[[wikilinks]]`, orphan pages, missing backlinks, sparse articles, missing frontmatter). | Free, no LLM |
| `/memory-query` | `query.py` (+ `config.py`) | Natural-language search over `knowledge/` via a `claude -p` subprocess that reads the index and synthesizes a cited answer. | Subprocess (subscription) |

## Why these aren't in the default kit

- **The daily-chronicle layer** (`/close-day` + `daily/`) was a v4 *default*; v5 demoted it because in long-running use it was the part that silently rotted — days went unclosed, and the rolling next-session-prompt froze while still looking authoritative. The v5 core replaces it with per-session handoffs (which can't go stale unnoticed). Keep the journal only if you genuinely want a day-by-day work diary.
- **`/memory-usage`** is the most valuable of the three commands, but its signal is thin until you have weeks of sessions and a real knowledge base — so it's an add-on, not a day-1 default.
- **`/memory-lint`** is wiki-gardening (broken links, backlinks). Useful for a large hand-linked base; noise for a casual user.
- **`/memory-query`** rarely earns its subprocess — you can just ask the agent "what do we know about X?" in normal conversation and it reads the index + concepts directly.

The old `/memory-compile` (auto-fold daily logs into wiki articles) was **removed entirely** — it was unreliable in practice, and the audit ritual already writes `knowledge/concepts/` articles directly, on your verbal "yes".

## How to enable

**The daily-chronicle layer** has its own one-`cp` enable step — see [`close-day-layer/README.md`](close-day-layer/README.md).

For the three power-user commands, copy them and their scripts into the live `.claude/` tree, then restart Claude Code:

```bash
mkdir -p .claude/memory/scripts
cp .kit/advanced/scripts/*.py   .claude/memory/scripts/
cp .kit/advanced/commands/*.md  .claude/commands/
```

That's it — `/memory-usage`, `/memory-lint`, `/memory-query` are now live slash commands. To disable, delete the copies from `.claude/`.

Enable only the ones you want: copy a single command's `.md` plus the script it names in its `## Execution` line (and `config.py` for `/memory-lint` and `/memory-query`, which import it).
