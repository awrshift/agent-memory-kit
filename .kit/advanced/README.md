# Advanced add-ons (opt-in)

The default kit is deliberately tiny: `/close-day` (the end-of-day audit ritual) and `/tour` cover the whole daily loop for most people. Everything in this folder is **opt-in** — power-user tooling for maintaining a knowledge base once it has grown.

> Unlike the rest of `.kit/` (which is pure documentation, safe to delete), this subfolder contains *functional* scripts and commands. They do nothing until you enable them.

## What's here

| Command | Script | What it does | Cost |
|---|---|---|---|
| `/memory-usage` | `aggregate_usage.py` + `usage_config.py` | Reads your session transcripts and reports **hot files** (used a lot) vs **cold candidates** (0 reads in 30 days → safe to archive). Turns "what can I prune?" into data. | Free, read-only |
| `/memory-lint` | `lint.py` | 5 structural health checks on `knowledge/` (broken `[[wikilinks]]`, orphan pages, missing backlinks, sparse articles, missing frontmatter). | Free, no LLM |
| `/memory-query` | `query.py` (+ `config.py`) | Natural-language search over `knowledge/` via a `claude -p` subprocess that reads the index and synthesizes a cited answer. | Subprocess (subscription) |

## Why these aren't in the default kit

- **`/memory-usage`** is the most valuable of the three, but its signal is thin until you have weeks of sessions and a real knowledge base — so it's an add-on, not a day-1 default.
- **`/memory-lint`** is wiki-gardening (broken links, backlinks). Useful for a large hand-linked base; noise for a casual user.
- **`/memory-query`** rarely earns its subprocess — you can just ask the agent "what do we know about X?" in normal conversation and it reads the index + concepts directly.

The old `/memory-compile` (auto-fold daily logs into wiki articles) was **removed entirely** — it was unreliable in practice, and `/close-day` already writes `knowledge/concepts/` articles directly, on your verbal "yes".

## How to enable

Copy the commands and scripts into the live `.claude/` tree, then restart Claude Code:

```bash
mkdir -p .claude/memory/scripts
cp .kit/advanced/scripts/*.py   .claude/memory/scripts/
cp .kit/advanced/commands/*.md  .claude/commands/
```

That's it — `/memory-usage`, `/memory-lint`, `/memory-query` are now live slash commands. To disable, delete the copies from `.claude/`.

Enable only the ones you want: copy a single command's `.md` plus the script it names in its `## Execution` line (and `config.py` for `/memory-lint` and `/memory-query`, which import it).
