---
name: memory-usage
description: Usage telemetry — which memory files are hot (actually read) vs cold (stale archival candidates). Use when the user says "/memory-kit:memory-usage", "what can I prune", "что можно почистить", or before a big memory audit.
allowed-tools: Bash, Read
model: sonnet
---

# /memory-kit:memory-usage

Generate `knowledge/usage-frequency.md` — a data-driven view of which files, skills, and tools you actually use.

Answers the question the `/close-session` audit otherwise has to guess: **what's safe to prune?** Files read often (recently) are hot and load-bearing; files with zero reads in 30 days are cold candidates for archival.

Reads your Claude Code session transcripts (`~/.claude/projects/<this-project>/**/*.jsonl`), filters out mechanical auto-loaded reads (MEMORY.md, CLAUDE.md, etc.) and collapses multi-edit bursts, so it measures deliberate use. Read-only — it writes one report and nothing else.

## When to use

- Periodically (monthly), or when `MEMORY.md` / `knowledge/concepts/` has grown and you want to know what's dead weight
- Right before a `/close-session` where you expect an archival proposal — feed the cold list into the audit

## Caveat

Frequency ≠ value. A cold concept may be foundational, just rarely re-read. Treat the cold list as one input to a proposal, never an auto-delete trigger. Needs a few weeks of real sessions before the signal is meaningful.

## Execution

!python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aggregate_usage.py"
