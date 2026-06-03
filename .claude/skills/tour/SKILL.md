---
name: tour
description: Interactive walkthrough of the Memory Kit system using the user's actual project files
---

# /tour — Interactive walkthrough

You are giving the user a guided tour of their Memory Kit. Use their actual files (not generic descriptions) so they see how the abstraction maps to concrete files.

## Tour structure (10-15 minutes)

### Stop 1 — CLAUDE.md (agent identity)
Open and read aloud the first few lines. Say: "This is my brain. I read it on every session start. It says who I am for this project, how to talk to you."

### Stop 2 — Session entry (NSP + backlog)
Open `context/next-session-prompt.md` and, if multi-project mode, `projects/<active>/BACKLOG.md`. Say: "This is yesterday-me's note (NSP) and today's plan (backlog). It's the first thing I read so I know where we left off."

### Stop 3 — Hot path (MEMORY.md)
Open `.claude/memory/MEMORY.md`. Say: "This is my hot cache. Date-tagged one-liners of patterns from recent sessions. Updates often — sometimes mid-session when I notice something worth keeping."

### Stop 4 — Rules (.claude/rules/)
List any `.claude/rules/*.md` files. If folder is empty (only `_example.md.disabled`), say: "This is where hard project rules live. 'Don't use X', 'always check Y'. They auto-load by keyword. Empty for now — they'll appear when you start dictating rules and I propose them on `/close-day`."

### Stop 5 — Knowledge concepts
List `knowledge/concepts/*.md`. Say: "Deep memory with facts. 'What's our typography scale', 'what we know about SEO for AI'. Reference articles. Empty now — I write them during `/close-day` when enough daily observations stack up around a topic."

### Stop 6 — Daily logs
Show `daily/`. Say: "Chronological session logs. The agent writes these via `/close-day` — you don't open them. Just ask me 'what did we do last Tuesday?' and I read them back."

### Stop 7 — Projects
List `projects/*/`. Say: "Each client or initiative gets a folder. BACKLOG.md for tasks, drop in any PDF or md as reference. Say 'we're working on <name>' and I switch context to that one."

### Stop 8 — Hooks
Mention `.claude/hooks/` exists but don't deep-dive. Say: "Five safety hooks run silently. They make sure state survives — block compaction until saved, log session lifecycle, periodic state-save prompts."

### Stop 9 — Operators
List the two default operators: `/close-day` and `/tour`. Say: "Type either to invoke. `/close-day` is the most important — that's the daily audit ritual where I propose what should be remembered, and it also catches up any days you forgot to close. There are a few power-user commands (search, hygiene, usage stats) parked in `.kit/advanced/` if you ever want them — but you don't need them to start."

## Closing

Ask: "Anything you want to drill into deeper? Or should we start with a real task — name your first project?"

## What you do NOT do

- **Don't read every file in full.** Show the first 5-10 lines so user sees the format, not the content.
- **Don't lecture.** This is a tour, not a manual. Each stop = 1-2 sentences.
- **Don't propose changes during the tour.** This is informational only. If user asks "can we change X" during tour — note it for after.
- **Don't skip stops based on emptiness.** Empty folders are part of the story — show them and explain when they fill.

## Length

Target 10-15 minutes total. If user is engaged and asks questions, fine — go longer. If user seems impatient, compress to 5 minutes by collapsing stops 4-7 into one "and these are the on-trigger layers" sweep.
