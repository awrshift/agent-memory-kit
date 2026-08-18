# Memory Kit — how you work in this repository

> Injected by the `memory-kit` plugin at every session start (and re-injected after compaction).
> It is versioned with the plugin, so there is nothing to paste into `CLAUDE.md`.

## Two invariants

**1 — The user talks. You write.** The user never opens `MEMORY.md`, a handoff, a rule or a
concept article. You propose in conversation, they say "yes", you write the file and say what you
wrote. If you catch yourself saying "add this to …" — rephrase as "I'll write it, confirm?".

**2 — Every memory entry carries a `[YYYY-MM-DD]` tag.** Dates are what make the audit possible:
without them you cannot see that a pattern showed up on three different days, and you cannot tell
a fresh fact from a rotten one. A stored fact about the OUTSIDE world (a price, an open ticket,
"the client is waiting") older than ~7 days is a hypothesis — re-check before acting on it.

## Where things live (in THIS repository)

| Layer | File | Answers | Loaded |
|---|---|---|---|
| Hot cache | `.claude/memory/MEMORY.md` | what repeats · where things stand | injected every session by the hook |
| Session log | `context/handoffs/<topic>-YYYY-MM-DD.md` | what happened, session by session | newest one injected; the rest on grep |
| Deep memory | `knowledge/concepts/*.md` + `knowledge/index.md` | facts and rationale by topic | index injected; articles on demand |
| Hard rules | `.claude/rules/*.md` | what must always / never happen | loaded by Claude Code itself |

Nothing else. No `wisdom/`, `playbooks/`, `patterns/` — a new memory layer is how this system dies.

## The caps (why the hook nags)

`MEMORY.md` is a HOT CACHE, not an archive: **180 lines / 32 KB / 3000 chars per line**. Three
caps because line count alone lies — content densifies into ever-longer lines while `wc -l` stays
flat. A tripped cap means run `/memory-kit:memory-audit` BEFORE other work.

- **The header is «current state»**, 2-3 sentences, REPLACED at every close — never a stack of
  "previous session" paragraphs. History belongs in handoffs.
- **Overflow flows out by promotion**: a pattern seen on 3+ distinct dates → a
  `knowledge/concepts/` article (facts + rationale) or a `.claude/rules/` file (a mechanical
  always/never, only once it is stable). Promoted entries get PRUNED from the cache.
- **One home per fact.** When a fact changes, grep its restatements and fix them in the same pass.
  A stale copy that still looks current is the #1 failure mode of agent memory.

## What else ships with the plugin (you have to know it exists to reach it)

**Operators**, all namespaced `/memory-kit:` — bodies load only on invoke: `close-session` ·
`memory-audit` (when a cap trips) · `system-audit` (the periodic seven-lens sweep) ·
`session-review` · `second-opinion` · `qa-sweep` · `setup` · `tour`.

**Depth, read on demand** from the plugin's `reference/` directory — free until you open it:
`orchestrator-fact-check` (a report is INPUT, never a fact) · `review-loop` (the diff gate + the
findings-class registry) · `parallel-development` (fan-out, worktree isolation, one integrator) ·
`doc-governance` (one SSOT per fact, the anti-drift rules) · `decisions-log` (the lean ledger) ·
`capability-map-sweep` (the "the library already does this" defect class). Delegating to
subagents? `templates/rules/orchestration.md` is the five always-loaded invariants — copy it into
`.claude/rules/` (a plugin cannot ship rules; `/memory-kit:setup` offers this).

## What you write freely vs what needs a "yes"

- **Freely (and you say so briefly):** `MEMORY.md` entries, the session handoff.
- **Ask first:** `.claude/rules/*.md` (always-loaded — every line costs context in every future
  session), `knowledge/concepts/*.md`, and any promotion. Repetition on 3 dates makes a
  CANDIDATE, not a rule.

## During the session

Observations happen in conversation; the ones worth keeping become one dated line in the hot
cache — say "saved" and move on. When context runs long, save state before it is compacted: the
PreCompact hook will block compaction until `MEMORY.md` is fresh and inside its caps.

Close with `/memory-kit:close-session`: capture → audit for 3+-date repetition → promote on the
user's yes → replace the header → write the handoff the next session opens with.
