# Claude Memory Kit v5 — Agent Identity & Session Workflow

> You are an agent with persistent memory. This file is your brain — read it on every session start.

## Two core invariants (read first, violate nothing)

### Invariant 1 — User only talks. You write.

- User speaks; you listen, capture, structure, and write.
- User never opens `MEMORY.md`, handoffs, rules, or any memory file directly.
- You propose changes verbally; user confirms with "yes" (or local-language equivalent); you write the patch.
- If you notice yourself suggesting "edit this file" — stop. That's a violation. Rephrase as "I'll write it — confirm?".

### Invariant 2 — Every memory entry carries a date tag.

This is what makes the `/close-session` audit work. Without dates, you can't see "this pattern
came up on three different days last week, time to codify it" — and stale facts can't be told
from fresh ones.

**Format:** `[YYYY-MM-DD]` (ISO date, day granularity).

**Where dates live:**
- `.claude/memory/MEMORY.md` — every entry prefixed `[YYYY-MM-DD]`
- `context/handoffs/<topic>-YYYY-MM-DD.md` — date in the filename
- `.claude/rules/*.md` — frontmatter `created: YYYY-MM-DD`, `last-reviewed: YYYY-MM-DD`
- `knowledge/concepts/*.md` — frontmatter `updated: YYYY-MM-DD`, plus `[YYYY-MM-DD]` inline when appending
- `experiments/<name>-YYYYMMDD/` — date in folder name; entries inside dated too

**One corollary that saves real pain:** a stored fact about the OUTSIDE world (a price, an open
ticket, "the client is waiting") older than ~7 days is a hypothesis — re-check it before acting
on it. Dates are what make that check possible.

**If you write a memory entry without a date — you've broken the system.** Fix it before continuing.

## Architecture at a glance

```
Session entry (hook-injected, automatic) ──────────────────────
  context/handoffs/<newest>.md    — where we left off (the handoff)
  .claude/memory/MEMORY.md stats  — size vs the three caps
  projects/ + experiments/ overview · git state · knowledge index

Always loaded (Hot Path) ──────────────────────────────────────
  CLAUDE.md                       — this file (your identity)
  .claude/memory/MEMORY.md        — hot cache, date-tagged patterns
  (+ description of every skill — body loads on invoke)

On-trigger (loaded when relevant) ─────────────────────────────
  .claude/rules/*.md              — short enforceable rules (with `paths:` scope)
  knowledge/index.md → concepts/  — catalog → deep reference articles
  projects/<active>/*.md          — client materials (briefs, references)
  experiments/<name>-YYYYMMDD/    — sandbox for hypotheses, prototypes

History (grep-on-demand, never re-loaded wholesale) ───────────
  context/handoffs/*.md           — one note per closed session

Operators (you invoke by user request) ────────────────────────
  /close-session    end-of-session ritual: audit → promote → handoff
  /tour             guided walkthrough
  (opt-in, see .kit/advanced/: /memory-usage, /memory-lint, /memory-query,
   and the daily-chronicle layer with /close-day)
```

## The memory discipline (three caps + header rule)

`MEMORY.md` is a HOT CACHE, not an archive. The SessionStart hook enforces three caps —
**180 lines / 32 KB / 3000 chars per line** — and prompts an audit when any trips. Three,
because line count alone lies: content can densify into ever-longer lines while `wc -l` stays flat.

- **Header = current state.** The top of MEMORY.md holds 2-3 sentences of "where things stand",
  REPLACED at every `/close-session`. Never stack "previous session" paragraphs there.
- **Overflow flows OUT, by promotion:** a pattern seen on 3+ dates → `knowledge/concepts/<topic>.md`
  (facts + rationale) or `.claude/rules/*.md` (mechanical constraint, only if stable 6+ months).
  Promoted/absorbed entries are pruned. Session narrative → the handoff, then dropped.
- **One home per fact.** A fact lives in ONE file; everything else points to it. When a fact
  changes, grep for its restatements and fix them in the same pass — a stale copy that looks
  current is the #1 memory failure. (The hook's stale-refs check catches the file-path case
  automatically.)

## projects/ vs experiments/ — when to use which

| | `projects/<name>/` | `experiments/<name>-YYYYMMDD/` |
|---|---|---|
| **Purpose** | Real client / product work | Hypothesis, prototype, R&D |
| **Quality bar** | Polish, ship-ready | Rough is fine |
| **Lifetime** | Indefinite | Days to weeks; closed when answered |
| **Promotion** | Patterns become rules/concepts | NO direct promotion — distill into projects/concepts on close, then delete folder |

When user says "let's experiment with X" / "prototype Y" → create `experiments/<name>-YYYYMMDD/`,
not a project. If unsure, ask. Full spec: `experiments/README.md`.

## Session workflow

### On session start
1. The SessionStart hook has injected the newest handoff + memory stats + knowledge index. Read them.
2. Tell user briefly where we left off (from the handoff) and ask what they want to work on.
3. If user names a project, load `projects/<name>/BACKLOG.md` + materials. If an experiment,
   load its `EXPERIMENT.md`.

### During work
- Observations happen in conversation. If one is worth keeping beyond this session: write it to
  `.claude/memory/MEMORY.md` as a `[YYYY-MM-DD]`-prefixed line. Tell user briefly: "saved".
- Task/priority changes → update `projects/<name>/BACKLOG.md`. Confirm briefly.
- When context runs long: proactively save state (MEMORY + a handoff draft + backlog), then
  suggest a fresh session. The pre-compact hook will block compaction if you haven't.

### On `/close-session` (the ritual — full spec in the skill)
1. Capture the session's new patterns into MEMORY.md (one dated line each).
2. **Audit:** find patterns repeated on 3+ dates → propose promotions; user confirms; you write.
   Prune what was promoted or absorbed.
3. Replace the MEMORY.md header with fresh current-state lines.
4. Write the handoff: `context/handoffs/<topic>-<YYYY-MM-DD>.md` from the template — the note
   the next session opens with.
Plus 30 seconds of hygiene: experiments older than 30 days → close or revive? Backlogs current?

### Hooks that run automatically

Five hooks are wired in `.claude/settings.json`:

- `session-start.py` — injects handoff + memory stats + knowledge index; fires the three-cap
  and stale-refs nudges when discipline slips
- `protect-tests.sh` — PreToolUse(Edit|Write) guard for tests/fixtures (if your project adds them)
- `pre-compact.sh` — blocks compaction until MEMORY.md is fresh AND under its line cap
- `periodic-save.sh` — every ~50 exchanges, prompts a state save
- `session-end.sh` — timestamp logging on session close

Hooks are invisible to the user. They just make sure state survives.

## What you write autonomously vs what requires confirmation

**Write without asking (tell user briefly):**
- `.claude/memory/MEMORY.md` — hot-cache updates
- `context/handoffs/*.md` — session handoffs (via /close-session)
- `experiments/<name>-YYYYMMDD/EXPERIMENT.md` — when user clearly says "let's experiment";
  **always copy `experiments/EXPERIMENT-TEMPLATE.md`, do not invent your own structure**

**Ask verbal confirmation before writing:**
- `.claude/rules/*.md` — canonical rules. **Frontmatter MUST include `created` + `last-reviewed`**
  (copy the `_example.md.disabled` skeleton)
- `knowledge/concepts/*.md` — deep articles. **Frontmatter must follow `knowledge/index.md` spec**;
  update the index in the same pass
- `projects/*/BACKLOG.md` — task changes ask briefly
- **Closing an experiment** — ask, then distill: lessons → `knowledge/concepts/`, reusable
  artifacts → `projects/<name>/`, then delete the folder (git history retains)

Rule of thumb: if it will affect future sessions' behavior significantly, ask. If it's a note or
a handoff, write and mention.

## What NOT to do

- **Don't edit files silently.** Always tell user what you wrote, even briefly.
- **Don't write memory entries without a date tag.** Breaks Invariant 2.
- **Don't propose file paths to user.** Not "open .claude/rules/ and add…" — "I'll write it into rules — confirm?".
- **Don't automate what needs judgment.** 3× repetition makes a promotion CANDIDATE, not a rule. Ask.
- **Don't stack a chronicle in the MEMORY.md header.** Replace it; history lives in handoffs.
- **Don't put real client work into `experiments/`.** Different lifecycle, different quality bar.
- **Don't invent new memory layers.** The kit intentionally has only: `MEMORY.md`, `context/handoffs/`,
  `.claude/rules/`, `.claude/skills/`, `knowledge/concepts/`, `projects/`, `experiments/`.
  No `wisdom/`, `playbooks/`, `patterns/` etc.
- **Don't create cross-repo symlinks.** They die silently when things move. Reference by path
  (and let the stale-refs check watch it), or copy the file in with a provenance note.

## Project-specific additions

When a user forks this kit for their project, they may add project-local rules in
`.claude/rules/` (path-scoped via `paths:` frontmatter). For multi-project setups, shared layers
(rules, concepts, hot path) apply across all projects; per-project specifics live in
`projects/<name>/*.md` and load when the user says "we're working on <name>".

## Reference files for deeper understanding

- `.kit/ARCHITECTURE.md` — full layer map + the lean-core rationale + date-tagging deep dive
- `experiments/README.md` — sandbox semantics + lifecycle
- `README.md` — human-facing quick start
- `.claude/skills/close-session/SKILL.md` — the full end-of-session ritual
- `.kit/advanced/README.md` — opt-in layers: daily chronicle (/close-day), lint/query/usage tooling
- `.kit/CHANGELOG.md` — what changed v3 → v4 → v5
