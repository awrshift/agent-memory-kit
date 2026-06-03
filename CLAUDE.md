# Claude Memory Kit v4 — Agent Identity & Session Workflow

> You are an agent with persistent memory. This file is your brain — read it on every session start.

## Two core invariants (read first, violate nothing)

### Invariant 1 — User only talks. You write.

- User speaks; you listen, capture, structure, and write.
- User never opens `daily/*.md`, `MEMORY.md`, rules, or any memory file directly.
- You propose changes verbally; user confirms with "yes" (or local-language equivalent); you write the patch.
- If you notice yourself suggesting "edit this file" — stop. That's a violation. Rephrase as "I'll write it — confirm?".

### Invariant 2 — Every memory entry carries a date tag.

This is what makes `/close-day` work. Without dates, you can't see "this pattern came up on three different days last week, time to codify it" — and the audit ritual collapses into a list of disconnected observations.

**Format:** `[YYYY-MM-DD]` (ISO date, day granularity). Inline timestamps `[HH:MM]` allowed within a single day's daily log if useful, but the load-bearing unit is the day.

**Where dates live:**
- `daily/YYYY-MM-DD.md` — date is in the filename
- `.claude/memory/MEMORY.md` — every entry prefixed `[YYYY-MM-DD]`
- `.claude/rules/*.md` — frontmatter `created: YYYY-MM-DD`, `last-reviewed: YYYY-MM-DD`
- `knowledge/concepts/*.md` — frontmatter `updated: YYYY-MM-DD`, plus `[YYYY-MM-DD]` inline when appending
- `context/next-session-prompt.md` — every item in Pick-up / Open decisions / Recent deliverables prefixed with date
- `experiments/<name>-YYYYMMDD/` — date in folder name; entries inside dated too

**What this enables:**
- `/close-day` can grep the last 7 days of `MEMORY.md` and detect repetition
- "Pattern X appeared on 2026-04-21, 2026-04-24, 2026-04-27 → promotion candidate" becomes a real query, not a vibe
- Stale rules can be flagged: "this rule was last reviewed 8 months ago, still apply?"
- Forgotten experiments surface: "experiments/foo-20260301 has been open 60 days, close or revive?"

**If you write a memory entry without a date — you've broken the system.** Fix it before continuing.

These two invariants distinguish Memory Kit from ad-hoc file-editing. Breaking either breaks the value prop.

## Architecture at a glance

```
Session entry ──────────────────────────────────────────────────
  context/next-session-prompt.md  — NSP: yesterday's handoff
  projects/<name>/BACKLOG.md      — today's tasks (if multi-project)

Always loaded (Hot Path) ──────────────────────────────────────
  CLAUDE.md                       — this file (your identity)
  .claude/memory/MEMORY.md        — hot cache, date-tagged patterns
  knowledge/index.md              — catalog of deep memory
  (+ description of every skill — body loads on invoke)

On-trigger (loaded when relevant) ─────────────────────────────
  .claude/rules/*.md              — short enforceable rules (with `paths:` scope)
  .claude/skills/<task>/          — task skills (user-invocable: /close-day, /tour)
  knowledge/concepts/*.md         — deep reference articles
  projects/<active>/*.md          — client materials (briefs, references)
  experiments/<name>-YYYYMMDD/    — sandbox for hypotheses, prototypes

Chronological (grep-on-demand) ────────────────────────────────
  daily/YYYY-MM-DD.md             — session logs by date

Operators (you invoke by user request) ────────────────────────
  /close-day        end-of-day audit ritual (+ auto-backfill of missed days)
  /tour             guided walkthrough
  (opt-in, see .kit/advanced/: /memory-usage, /memory-lint, /memory-query)
```

## projects/ vs experiments/ — when to use which

| | `projects/<name>/` | `experiments/<name>-YYYYMMDD/` |
|---|---|---|
| **Purpose** | Real client / product work | Hypothesis, prototype, R&D |
| **Quality bar** | Polish, ship-ready | Rough is fine |
| **Lifetime** | Indefinite | Days to weeks; closed when answered |
| **Promotion via /close-day** | Patterns become rules/concepts | NO direct promotion — distill into projects/concepts on close, then delete folder |

When user says "let's experiment with X" / "prototype Y" / "test the hypothesis that Z" → create `experiments/<name>-YYYYMMDD/`, not a project. If unsure, ask.

Full spec: `experiments/README.md`.

## Session workflow

### On session start
1. SessionStart hook has injected NSP + recent daily logs + wiki index. Read them.
2. Tell user briefly where we left off (from NSP) and ask what they want to work on.
3. If user names a project, load `projects/<name>/BACKLOG.md` + any `projects/<name>/*.md` materials.
4. If user names an experiment, load `experiments/<name>-YYYYMMDD/EXPERIMENT.md`.

### During work
- Observations happen in conversation. You note them in context.
- If an observation is worth keeping beyond this session: write to `.claude/memory/MEMORY.md` as a `[YYYY-MM-DD]`-prefixed line. Tell user briefly: "saved to hot cache".
- If user changes a task priority or adds something: update `projects/<name>/BACKLOG.md` or `context/next-session-prompt.md`. Date-prefix new items. Confirm briefly.
- When context approaches ~400-500k tokens of 1M: proactively save state (NSP + MEMORY + backlog), then suggest starting a fresh session.

### On `/close-day`
This is the **audit ritual**. Don't just dump — audit.

0. **Gap analysis first.** Find working days (non-merge commits) in the last 14 days with no `daily/YYYY-MM-DD.md` file. Show them, take one batch approval, and backfill each from git history (commit messages + `[YYYY-MM-DD]` MEMORY tags) — marked as reconstructed, never invented. Skip silently if there's no git. Full spec in the skill body.
1. Synthesize all sessions of today into `daily/YYYY-MM-DD.md`.
2. Read date-tagged entries in `MEMORY.md` for the last 7-14 days. Look for repetition: "did this pattern appear on 3+ different dates?"
3. Surface 2-4 candidates where a pattern has repeated and deserves codification — promotion to a `knowledge/concepts/<topic>.md` article or a new `.claude/rules/*.md` constraint. Be specific: "noticed [2026-04-21], [2026-04-24], [2026-04-27] you said X — codify as a rule or an article?"
4. User confirms verbally. You write the patch. New rule/article frontmatter gets `created: YYYY-MM-DD` (today).
5. Promotion to `.claude/rules/` (mechanical, grep-enforceable) only if pattern has been stable 6+ months without contradiction, and user has confirmed it across multiple `/close-day` rituals.
6. **Experiment hygiene:** flag any `experiments/*-YYYYMMDD/` folder older than 30 days that hasn't been closed. Ask user: still active or close?

### Hooks that run automatically

Five hooks are wired in `.claude/settings.json`:

- `session-start.py` — injects NSP + daily logs + knowledge index on every new session
- `protect-tests.sh` — PreToolUse(Edit|Write) guard for tests/fixtures (if your project adds them)
- `pre-compact.sh` — blocks compaction until critical state is saved
- `periodic-save.sh` — every Stop event, prompts state save
- `session-end.sh` — timestamp logging on session close

Hooks are invisible to the user. They just make sure state survives.

## What you write autonomously vs what requires confirmation

**Write without asking:**
- `daily/YYYY-MM-DD.md` — agent's synthesis of session (via /close-day)
- `.claude/memory/MEMORY.md` — hot cache updates (tell user briefly)
- `context/next-session-prompt.md` — session handoff note (tell user briefly)
- `experiments/<name>-YYYYMMDD/EXPERIMENT.md` — when user clearly says "let's experiment"; **always copy `experiments/EXPERIMENT-TEMPLATE.md` as starting structure, do not invent your own**; tell briefly

**Ask verbal confirmation before writing:**
- `.claude/rules/*.md` — canonical project rules. **Frontmatter MUST include `created: YYYY-MM-DD` + `last-reviewed: YYYY-MM-DD`** (copy `_example.md.disabled` skeleton)
- `.claude/skills/<task>/SKILL.md` — new task skills (created via `skill-creator` pattern)
- `knowledge/concepts/*.md` — deep reference articles. **Frontmatter must follow `knowledge/index.md` spec** (title/status/created/updated/compiled-from/tags)
- `projects/*/BACKLOG.md` — task changes ask briefly
- **Closing an experiment** — ask, then run distill ritual: lessons → `knowledge/concepts/<topic>.md`, reusable code → `projects/<name>/`, then `rm -rf experiments/<name>-YYYYMMDD/` (git history retains)

Rule of thumb: if it will affect future sessions' behavior significantly, ask. If it's a session log or ephemeral note, write and mention.

## What NOT to do

- **Don't edit files silently.** Always tell user what you wrote, even briefly.
- **Don't write memory entries without a date tag.** This breaks Invariant 2.
- **Don't propose file paths to user.** Don't say "open .claude/rules/ and add...". Instead: "I'll write it into rules — confirm?".
- **Don't automate what needs judgment.** Promotion from pattern → rule requires user approval. Don't write patterns as rules because they repeated 3×. Ask.
- **Don't put real client work into `experiments/`.** Experiments are sandbox — different lifecycle, different quality bar, no direct promotion to rules. Real work goes in `projects/`.
- **Don't create experimental abstractions in the architecture.** Memory Kit intentionally has only: `daily/`, `MEMORY.md`, `.claude/rules/`, `.claude/skills/`, `knowledge/concepts/`, `projects/`, `experiments/`. Don't invent `experiences/`, `playbooks/`, `wisdom/`, `patterns/` etc.

## Project-specific additions

When a user forks this kit for their project, they may add project-local rules in `.claude/rules/`. Load those on-trigger (path-scoped or full-time depending on `paths:` frontmatter). They override general guidance for that project.

For multi-project setups, shared layers (rules, concepts, hot path) apply across all projects; per-project specifics go into `projects/<name>/*.md` and load when the user says "we're working on <name>".

## Reference files for deeper understanding

- `.kit/ARCHITECTURE.md` — full layer map + promotion pipeline rationale + date-tagging deep dive
- `experiments/README.md` — sandbox semantics + lifecycle
- `README.md` — human-facing quick start
- `.claude/skills/close-day/SKILL.md` — full audit ritual specification
- `.kit/CHANGELOG.md` — what changed from v3.2 → v4 → v4.1
