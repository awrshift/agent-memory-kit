---
name: tour
description: Interactive walkthrough of the Memory Kit system using the user's actual project files. Use when the user says "/memory-kit:tour", "give me a tour", "покажи как это работает", or right after /memory-kit:setup.
allowed-tools: Read, Glob, Grep, Bash
model: sonnet
---

# /memory-kit:tour — Interactive walkthrough

You are giving the user a guided tour of their Memory Kit. Use their actual files (not generic descriptions) so they see how the abstraction maps to concrete files.

## Tour structure (10-15 minutes)

### Stop 1 — the working agreement (injected, not a file in this repo)
Run `/context` or point at the session's opening block. Say: "The rules I work by ship with the plugin and are injected at every session start — there's nothing for you to maintain. Your own project rules, if you ever want any, live in `.claude/rules/`."

### Stop 2 — Session entry (handoff + backlog)
Open the newest `context/handoffs/*.md` (or the template if none yet) and, if multi-project mode, `projects/<active>/BACKLOG.md`. Say: "This is the note the previous session left for me — the handoff. The start-hook injects the newest one automatically, so I open every session already knowing where we left off."

### Stop 3 — Hot path (MEMORY.md)
Open `.claude/memory/MEMORY.md`. Say: "This is my hot cache. Date-tagged one-liners of patterns from recent sessions; the header on top is the current state of work, replaced at every close. A hook watches three size caps so this file physically can't silently bloat."

### Stop 4 — Rules (.claude/rules/)
List any `.claude/rules/*.md` files. If folder is empty (only `_example.md.disabled`), say: "This is where hard project rules live. 'Don't use X', 'always check Y'. They auto-load by keyword. Empty for now — they'll appear when you start dictating rules and I propose them on `/memory-kit:close-session`."

### Stop 5 — Knowledge concepts
List `knowledge/concepts/*.md`. Say: "Deep memory with facts. 'What's our typography scale', 'what we know about SEO for AI'. Reference articles. Empty now — I write them during `/memory-kit:close-session` when a pattern has repeated on three-plus dates and you say yes."

### Stop 6 — Handoff history
Show `context/handoffs/`. Say: "One note per closed session — my session diary. You never open them; just ask 'what did we do last Tuesday?' and I read them back."

### Stop 7 — Projects
List `projects/*/`. Say: "Each client or initiative gets a folder. BACKLOG.md for tasks, drop in any PDF or md as reference. Say 'we're working on <name>' and I switch context to that one."

### Stop 8 — Hooks
Don't deep-dive — the hooks ship inside the plugin, there is nothing in this repo to maintain. Say: "Four hooks run silently: one injects your memory and the working rules at every session start, one blocks compaction until state is saved, one asks before an existing test gets edited, one logs the close."

### Stop 9 — Operators
List what this plugin adds: `/memory-kit:close-session`, `/memory-kit:tour`, `/memory-kit:setup`, plus `/memory-kit:memory-lint` and `/memory-kit:memory-usage` for later. Say: "`/memory-kit:close-session` is the one that matters — the end-of-session ritual where I audit what happened, propose what's worth remembering forever, and leave the handoff note for next time. Two sibling plugins exist when you need them: `memory-kit-orchestration` for building with subagents, `memory-kit-qa` for probing a running product. You don't need either to start."

## Closing

Ask: "Anything you want to drill into deeper? Or should we start with a real task — name your first project?"

## What you do NOT do

- **Don't read every file in full.** Show the first 5-10 lines so user sees the format, not the content.
- **Don't lecture.** This is a tour, not a manual. Each stop = 1-2 sentences.
- **Don't propose changes during the tour.** This is informational only. If user asks "can we change X" during tour — note it for after.
- **Don't skip stops based on emptiness.** Empty folders are part of the story — show them and explain when they fill.

## Length

Target 10-15 minutes total. If user is engaged and asks questions, fine — go longer. If user seems impatient, compress to 5 minutes by collapsing stops 4-7 into one "and these are the on-trigger layers" sweep.
