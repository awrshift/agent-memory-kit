# Memory Kit v4 — Architecture

> Full architecture with rationale. Read after CLAUDE.md for depth.

## The core invariant

**User only talks. Agent captures, proposes, writes.** This is the one rule that makes everything else consistent.

If an architectural decision violates this invariant (e.g., «user should periodically review memory files and edit them»), it's wrong by definition.

## Layer map (what lives where)

v4 aligns tightly with Anthropic-canonical Claude Code primitives. Every layer maps to a native concept documented at `code.claude.com/docs`.

```
╔══════════════════════════════════════════════════════════════╗
║  SESSION ENTRY (loaded automatically)                        ║
║  ──────────────────────────────────────────────────────────  ║
║  context/next-session-prompt.md                              ║
║      ↓ "where we left off, what's next"                      ║
║  projects/<active>/BACKLOG.md                                ║
║      ↓ "today's task queue"                                  ║
╠══════════════════════════════════════════════════════════════╣
║  HOT PATH (always in context)                                ║
║  ──────────────────────────────────────────────────────────  ║
║  CLAUDE.md                  — agent identity                 ║
║  .claude/memory/MEMORY.md   — date-tagged patterns           ║
║  knowledge/index.md         — deep-memory catalog            ║
║  (+ every skill's `description` — body loads on invoke)      ║
╠══════════════════════════════════════════════════════════════╣
║  ON-TRIGGER (loaded when relevant)                           ║
║  ──────────────────────────────────────────────────────────  ║
║  .claude/rules/*.md             — short enforceable rules    ║
║                                   (unconditional or path-    ║
║                                   scoped via `paths:`)       ║
║  .claude/skills/<task>/SKILL.md — task skills (user-         ║
║                                   invocable; /close-day,     ║
║                                   /tour, etc.)               ║
║  knowledge/concepts/*.md        — deep reference articles    ║
║  projects/<active>/*.md         — client materials (PDFs,    ║
║                                   briefs, references)        ║
╠══════════════════════════════════════════════════════════════╣
║  CHRONOLOGICAL (grep-on-demand, not auto-loaded)             ║
║  ──────────────────────────────────────────────────────────  ║
║  daily/YYYY-MM-DD.md      — session logs by date             ║
╠══════════════════════════════════════════════════════════════╣
║  OPERATORS (invoked by user speech)                          ║
║  ──────────────────────────────────────────────────────────  ║
║  /close-day       end-of-day AUDIT ritual + backfill         ║
║  /tour            interactive walkthrough                    ║
║  ── opt-in (.kit/advanced/, copy into .claude/ to enable) ── ║
║  /memory-usage    hot/cold telemetry (archival candidates)   ║
║  /memory-lint     structural health checks                   ║
║  /memory-query    natural-language search                    ║
╚══════════════════════════════════════════════════════════════╝
```

## What each layer is FOR (and is NOT)

### CLAUDE.md — agent identity
**Is:** stable DNA of the project. Who the agent is, what tone, what's forbidden, how it thinks.
**Is not:** daily notes. Doesn't change often. Target ≤ 200 lines (Anthropic guidance).

### .claude/memory/MEMORY.md — hot cache
**Is:** date-tagged patterns that have already been noticed 2+ times. Short strings. Cross-session accumulator. First 200 lines / 25KB auto-loaded (Anthropic auto-memory contract).
**Is not:** full logs (those live in daily/). Not detailed articles.

### .claude/rules/*.md — rules
**Is:** mechanical constraints. "Don't use X", "Always check Y". Short. Enforceable by grep/linter in principle. Can be `paths:`-scoped to apply only when working with matching files.
**Is not:** advice. Not judgment heuristics. Not raw facts (those are concepts).

### .claude/skills/<task>/SKILL.md — task skills
**Is:** repeatable workflow the user (or agent) invokes with `/task-name`. Operators like `/close-day`, `/tour`. Slash-command files in `.claude/commands/` are thin wrappers that invoke these.
**Is not:** knowledge or rules. If it's "do these steps" → task skill. If it's "always X" → rule. If it's "what is X" → concept.

### knowledge/concepts/*.md — deep reference
**Is:** facts + rationale, topic-oriented. "Our typography scale: 43 paired sub-tokens. Sizes, line heights, weights. Reasoning per level."
**Is not:** workflow methodology (that's a task skill or rule). Not date-tagged short notes (that's MEMORY.md).

### projects/<name>/ — per-project scope
**Is:** everything specific to one client or project. `BACKLOG.md` (tasks), any `*.md` or `*.pdf` user has uploaded as reference.
**Is not:** shared knowledge. Don't put brand-system stuff here if it applies across projects. Not a sandbox for prototypes (that's `experiments/`).

### experiments/<name>-YYYYMMDD/ — sandbox
**Is:** R&D folder for hypotheses, prototypes, throwaway research. `EXPERIMENT.md` (hypothesis + result), optional code, notes, screenshots. Date in folder name.
**Is not:** real client work (that's `projects/`). Not a long-term home — closed experiments are distilled into `knowledge/concepts/` (lessons) and `projects/` (code), then deleted (git history remembers).

Why a separate layer? Different lifecycle (days, not indefinite), different quality bar (rough OK), different relationship to `/close-day` audit (no direct promotion to rules — distill first, then close). Full spec: `experiments/README.md`.

### daily/YYYY-MM-DD.md — session archive
**Is:** agent-written synthesis of sessions (via `/close-day`). Chronological.
**Is not:** manually curated. Not a wiki.

## Date-tagging convention (load-bearing)

Every memory entry across the kit carries an ISO date tag (`[YYYY-MM-DD]`). This is not stylistic — it's the foundation that lets `/close-day` detect cross-session patterns and propose promotions.

### Where dates live

| Layer | Date placement |
|---|---|
| `daily/YYYY-MM-DD.md` | filename |
| `.claude/memory/MEMORY.md` | `[YYYY-MM-DD]` prefix on every entry |
| `.claude/rules/*.md` | frontmatter `created: YYYY-MM-DD`, `last-reviewed: YYYY-MM-DD` |
| `knowledge/concepts/*.md` | frontmatter `updated: YYYY-MM-DD`, plus `[YYYY-MM-DD]` inline when appending sections |
| `context/next-session-prompt.md` | `[YYYY-MM-DD]` prefix on each Pick-up / Open decisions / Recent deliverables item |
| `experiments/<name>-YYYYMMDD/` | folder name; entries inside dated too |

### Why this matters

Without dates, every memory entry is timestamp-less noise. With dates, the agent can answer:

- "Has this pattern come up on multiple distinct days?" → MEMORY grep for date diversity
- "When did this rule get codified — is it still fresh?" → frontmatter `last-reviewed`
- "What experiments have been open >30 days?" → folder name parse
- "What was decided last Tuesday?" → daily/YYYY-MM-DD lookup
- "Has this rule been contradicted recently?" → cross-reference rule `last-reviewed` against recent MEMORY entries

`/close-day` Phase 2 audit is built on these queries. Without date-tagging, the ritual collapses to "synthesize today" — the cross-session intelligence dies.

### Format rules

- ISO 8601 daily granularity is the base unit: `[2026-04-27]`
- Inline `[HH:MM]` allowed within a single day's daily log if useful, never required
- Time zones — local. Don't mix UTC and local in the same project
- Don't use relative dates ("yesterday", "last week") in stored memory — they decay. Always absolute

### When the agent writes without a date — it's a bug

If you find a MEMORY entry, NSP item, or rule frontmatter without a date, fix it before continuing. This is the single rule that makes the rest of the system work.

## The promotion pipeline (pattern → law)

Three phases. All agent-driven.

```
  Liquid             ──→  Amber              ──→  Crystal
  daily/*.md              MEMORY.md                .claude/rules/*.md
                          (date-tagged)            (grep-enforceable)
                                                   OR
                                                   knowledge/concepts/*.md
                                                   (deep reference article)
```

### Phase 1 — Liquid (daily/)
Observation mentioned in a session. Agent captures in today's daily log. Candidate, nothing more.

### Phase 2 — Amber (MEMORY.md)
Pattern repeats within the session OR across sessions. Agent writes a date-tagged string to `MEMORY.md`. Tells user briefly: "saved". User does nothing.

### Phase 3 — Crystal (rules/ or concepts/)
On `/close-day`, agent surfaces candidates from amber. User says "yes" → agent writes:
- A canonical rule into `.claude/rules/<name>.md` (if it's mechanical / enforceable / always-or-never), or
- A reference article into `knowledge/concepts/<topic>.md` (if it's facts + rationale to remember).

Promotion is the **agent-driven audit ritual**. Not automatic detection, not manual editing. Agent has full context at end of day; agent does the writing; user only confirms.

### Why no automation for 3× detection?

Earlier drafts considered `experiences/` staging + a `promote-patterns.py` background script to auto-detect 3× repetitions. Killed 2026-04-24 because:

1. **Cross-session detection is unreliable.** Without a persistent background process, agent can't reliably match semantics across session boundaries.
2. **The automation solved a hypothetical problem.** After one day the scaffold had zero entries.
3. **The ritual is better.** `/close-day` runs agent-with-full-context at end of day. Cross-session patterns get noticed WITH intent, not via fragile signature matching.

The kill reduced complexity + restored the «user only talks» invariant that an automated background detector would have threatened.

## The audit ritual (mechanics of /close-day)

```
User types: /close-day
    │
    ▼
Agent synthesizes today's sessions → daily/YYYY-MM-DD.md
    │
    ▼
Agent reads MEMORY.md (date-tagged cross-session patterns)
Agent reads today's daily
Agent reads existing knowledge/concepts/*.md + .claude/rules/*.md
    │
    ▼
Agent audits: which today's patterns match or extend MEMORY.md?
              Which deserve a concept article or a hard rule?
    │
    ▼
Agent surfaces 0-4 candidates to user verbally:
  "noticed Y three times this week — codify as a rule?"
  "concept X already exists, update it with today's observation?"
  "this pattern contradicts rule Z — has something changed?"
    │
    ▼
User responds verbally:
  "yes" → agent writes the patch (new entry, modification, etc.)
  "no" / "not now" → agent acknowledges, doesn't write
  "show again" → agent shows proposed patch text
    │
    ▼
Agent writes patches sequentially, confirms each completion
```

Key property: **user never opens a file during the entire ritual.** They talk, agent writes.

## Multi-project architecture

One agent, many projects. Shared layers (rules, concepts, hot path) apply across all projects. Per-project layers (BACKLOG.md, client materials) are scoped.

```
Shared (loaded always):
  CLAUDE.md, MEMORY.md, knowledge/, .claude/rules/, .claude/skills/<task>/

Project-scoped (loaded when user names the project):
  projects/<active>/BACKLOG.md
  projects/<active>/*.md    (client brief, brand guide, notes)
  projects/<active>/*.pdf   (user-uploaded references)
```

Switch command (in conversation): "we're working on client-a" → agent unloads client-b materials, loads client-a. For project-scoped rules, use `paths: [projects/client-a/**]` frontmatter on the rule file.

## Hooks (automatic, no user action)

Five hooks wired in `.claude/settings.json`:

- **session-start.py** — on every new Claude session, injects NSP + recent daily logs + knowledge index into agent context
- **protect-tests.sh** — PreToolUse(Edit|Write) guard for `tests/fixtures/canonical/` (if your project adds them)
- **pre-compact.sh** — when context is about to compact, blocks until agent has saved state to MEMORY.md + NSP
- **periodic-save.sh** — every Stop event, prompts agent to save new patterns
- **session-end.sh** — SessionEnd timestamp logging

Hooks are invisible to the user. They just make sure state survives.

## Naming discipline

File names are in English for canonical compatibility. Agent references them in Russian conversation naturally. No need to teach the user English filenames.

Per-project folders can use any naming: `projects/client-nestle/`, `projects/nachalo/`, `projects/mvp-launch/` — whatever the user prefers.

## What's NOT in the architecture (by design)

- **`experiences/`** — over-engineered staging layer, deleted v4
- **`promote-patterns.py`** — background detection script, replaced by /close-day ritual
- **`playbooks/`** — draft-era separate directory for role wisdom; killed in v4.0.0-alpha.2
- **Role-guidance reference skills** (`<role>-guidance/SKILL.md` with `user-invocable: false`) — shipped in v4.0.0, killed in v4.1.0 as kit-shipped seeds. Pattern still works if you want to add your own per-project, but the kit doesn't ship templates
- **`/memory-audit` operator** — was paired with role-guidance; removed in v4.1.0
- **`/memory-compile` operator** — auto-folding daily logs into wiki articles was unreliable; removed in v4.2.0. `/close-day` writes `knowledge/concepts/` articles directly, on user "yes".
- **`/memory-lint`, `/memory-query`, `/memory-usage` in the default surface** — moved to opt-in `.kit/advanced/` in v4.2.0. Default operators are just `/close-day` + `/tour`; the rest are power-user tooling you copy in when your knowledge base has grown.
- **`knowledge/connections/` + `knowledge/meetings/`** — extra subdirs that nobody filled; collapsed into single `knowledge/concepts/` in v4.1.0
- **Custom trigger keyword tables in CLAUDE.md** — Claude auto-invokes skills from their `description`; no hand-maintained routing
- **`wisdom/`**, **`lessons/`** — synonyms of existing layers, kept out
- **Automatic rule generation** — rules are user-approved only, never auto-written

### Adding role-guidance yourself (advanced)

If you want the role-guidance pattern back for your project, create skills under `.claude/skills/<role>-guidance/SKILL.md` with `user-invocable: false` and a keyword-rich `description`. Claude will auto-invoke them on description match. The kit doesn't seed templates — what works for content marketing is wrong for SaaS dev is wrong for editorial work, so a generic seed is noise.

## Related

- `README.md` — human-facing value prop (project root)
- `CLAUDE.md` — agent-facing session workflow (project root)
- `.kit/CHANGELOG.md` — version history including v4.1.0 minimization
- Anthropic docs: `code.claude.com/docs/en/skills`, `code.claude.com/docs/en/memory`, `code.claude.com/docs/en/best-practices`
