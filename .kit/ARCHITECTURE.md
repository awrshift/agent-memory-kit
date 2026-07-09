# Memory Kit v5 — Architecture

> Full architecture with rationale. Read after CLAUDE.md for depth.

## The core invariant

**User only talks. Agent captures, proposes, writes.** This is the one rule that makes everything else consistent.

If an architectural decision violates this invariant (e.g., «user should periodically review memory files and edit them»), it's wrong by definition.

## Layer map (what lives where)

v5 is the **lean core**: the default surface is two operators (`/close-session` + `/tour`) and one
"where we left off" mechanism (per-session handoffs). Everything heavier is opt-in in `.kit/advanced/`.
Every layer still maps to a native Claude Code concept documented at `code.claude.com/docs`.

```
╔══════════════════════════════════════════════════════════════╗
║  SESSION ENTRY (injected automatically by session-start.py)  ║
║  ──────────────────────────────────────────────────────────  ║
║  1. Memory-discipline nudges — ONLY when they fire           ║
║       (the three MEMORY.md caps + stale file references)     ║
║  2. Session stats — MEMORY.md size vs caps,                  ║
║       projects/experiments overview, git state              ║
║  3. context/handoffs/<newest>.md — "where we left off"       ║
║  4. knowledge/index.md — the catalog of deep memory          ║
╠══════════════════════════════════════════════════════════════╣
║  HOT PATH (always in context)                                ║
║  ──────────────────────────────────────────────────────────  ║
║  CLAUDE.md                  — agent identity                 ║
║  .claude/memory/MEMORY.md   — date-tagged patterns +         ║
║                               a current-state header         ║
║  (+ every skill's `description` — body loads on invoke)      ║
╠══════════════════════════════════════════════════════════════╣
║  ON-TRIGGER (loaded when relevant)                           ║
║  ──────────────────────────────────────────────────────────  ║
║  .claude/rules/*.md             — short enforceable rules    ║
║                                   (unconditional or path-    ║
║                                   scoped via `paths:`)       ║
║  .claude/skills/<task>/SKILL.md — task skills (user-         ║
║                                   invocable; /close-session, ║
║                                   /tour)                     ║
║  knowledge/concepts/*.md        — deep reference articles    ║
║  projects/<active>/*.md         — client materials (PDFs,    ║
║                                   briefs, references)        ║
╠══════════════════════════════════════════════════════════════╣
║  HANDOFF HISTORY (grep-on-demand, not auto-loaded wholesale) ║
║  ──────────────────────────────────────────────────────────  ║
║  context/handoffs/<topic>-YYYY-MM-DD.md                      ║
║      — one immutable note per closed session; only the       ║
║        NEWEST is injected at session entry                   ║
╠══════════════════════════════════════════════════════════════╣
║  OPERATORS (invoked by user speech)                          ║
║  ──────────────────────────────────────────────────────────  ║
║  /close-session   end-of-session AUDIT ritual + handoff      ║
║  /tour            interactive walkthrough                    ║
║  ── opt-in (.kit/advanced/, copy into .claude/ to enable) ── ║
║  /memory-usage    hot/cold telemetry (archival candidates)   ║
║  /memory-lint     structural health checks                   ║
║  /memory-query    natural-language search                    ║
║  /close-day       day-by-day journal layer (close-day-layer) ║
╚══════════════════════════════════════════════════════════════╝
```

## What each layer is FOR (and is NOT)

### CLAUDE.md — agent identity
**Is:** stable DNA of the project. Who the agent is, what tone, what's forbidden, how it thinks.
**Is not:** session notes. Doesn't change often.

### .claude/memory/MEMORY.md — hot cache
**Is:** a current-state header (2-3 sentences, replaced every close) followed by date-tagged
patterns that have already been noticed 2+ times. Short strings. Cross-session accumulator.
Held under three caps (below).
**Is not:** full session logs (those live in the handoffs). Not detailed articles.

### context/handoffs/*.md — session handoffs
**Is:** one short note per closed session, `<topic>-YYYY-MM-DD.md`, written at `/close-session`
from `HANDOFF-TEMPLATE.md`. The SessionStart hook injects the NEWEST one, so tomorrow's session
opens already knowing where you left off. Older handoffs stay as searchable history.
**Is not:** a rolling file that gets overwritten (that was the v4 NSP — retired, see below). Not
a chronicle stacked into MEMORY.md's header.

### .claude/rules/*.md — rules
**Is:** mechanical constraints. "Don't use X", "Always check Y". Short. Enforceable by grep/linter in principle. Can be `paths:`-scoped to apply only when working with matching files.
**Is not:** advice. Not judgment heuristics. Not raw facts (those are concepts).

### .claude/skills/<task>/SKILL.md — task skills
**Is:** repeatable workflow the user (or agent) invokes with `/task-name`. Default operators are
`/close-session` and `/tour`. Claude Code auto-registers each skill from its `SKILL.md`; an optional
thin wrapper in `.claude/commands/<name>.md` can invoke one (the opt-in `.kit/advanced/` commands use that form).
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

Why a separate layer? Different lifecycle (days, not indefinite), different quality bar (rough OK), different relationship to the `/close-session` audit (no direct promotion to rules — distill first, then close). Full spec: `experiments/README.md`.

## Date-tagging convention (load-bearing)

Every memory entry across the kit carries an ISO date tag (`[YYYY-MM-DD]`). This is not stylistic — it's the foundation that lets `/close-session` detect cross-session patterns and propose promotions.

### Where dates live

| Layer | Date placement |
|---|---|
| `.claude/memory/MEMORY.md` | `[YYYY-MM-DD]` prefix on every entry |
| `context/handoffs/<topic>-YYYY-MM-DD.md` | date in the filename |
| `.claude/rules/*.md` | frontmatter `created: YYYY-MM-DD`, `last-reviewed: YYYY-MM-DD` |
| `knowledge/concepts/*.md` | frontmatter `updated: YYYY-MM-DD`, plus `[YYYY-MM-DD]` inline when appending sections |
| `experiments/<name>-YYYYMMDD/` | folder name; entries inside dated too |

### Why this matters

Without dates, every memory entry is timestamp-less noise. With dates, the agent can answer:

- "Has this pattern come up on multiple distinct days?" → MEMORY grep for date diversity
- "When did this rule get codified — is it still fresh?" → frontmatter `last-reviewed`
- "What experiments have been open >30 days?" → folder name parse
- "Where did we leave off, and when?" → the newest handoff's date in its filename
- "Has this rule been contradicted recently?" → cross-reference rule `last-reviewed` against recent MEMORY entries

The `/close-session` audit (Step 2) is built on these queries. Without date-tagging, the ritual collapses to "capture today" — the cross-session intelligence dies.

### Format rules

- ISO 8601 daily granularity is the base unit: `[2026-04-27]`
- Time zones — local. Don't mix UTC and local in the same project
- Don't use relative dates ("yesterday", "last week") in stored memory — they decay. Always absolute

### When the agent writes without a date — it's a bug

If you find a MEMORY entry or rule frontmatter without a date, fix it before continuing. This is the single rule that makes the rest of the system work.

## Why three caps on MEMORY.md (line count alone lies)

`MEMORY.md` is a HOT CACHE, not an archive. The `session-start.py` hook enforces **three
independent caps** and prompts an audit when any trips:

| Cap | Threshold | Catches |
|---|---|---|
| Line count | 180 lines | the obvious "too many entries" case |
| Byte size | 32 KB | dense content that stays under the line cap |
| Longest line | 3000 chars | a single giant "chronicle" line |

Why three and not just a line count? **Because line count alone lies.** In real long-running use
we hit a MEMORY.md that packed **51.5 KB into 152 lines** — comfortably under a 180-line cap, yet
already unreadable, because content had densified into ever-longer lines instead of more of them.
A line-count check waves that through. The byte and longest-line caps catch the class of bloat the
line count can't see. When any cap trips, the next session opens with an audit prompt instead of
silently growing.

### Header discipline

The top of `MEMORY.md` (everything above the first `---`) is «current state of work» — 2-3
sentences, **REPLACED** at every `/close-session`, never a stack of "previous session" paragraphs.
Per-session detail belongs in the handoff, not the header. A header that accretes history is how a
"current state" file silently becomes a chronicle nobody trusts.

## The promotion flow (pattern → law)

Promotion is agent-driven, on `/close-session`, always on the user's verbal "yes".

```
  observed in         →  MEMORY.md            →  .claude/rules/*.md
  conversation           (date-tagged line)      (grep-enforceable, stable 6+ months)
                                                  OR
                                                  knowledge/concepts/*.md
                                                  (deep reference article)
```

1. **Captured.** Something worth keeping comes up in a session. The agent writes a date-tagged
   one-liner to `MEMORY.md` and tells the user "saved". The user does nothing.
2. **Audited.** On `/close-session`, the agent reads the date-tagged entries and looks for
   repetition: **did this pattern appear on 3+ different dates?** It surfaces 2-4 candidates,
   specific and dated: "noticed [date], [date], [date] you said X — codify as a rule or a concept?"
3. **Promoted on "yes".** The user confirms → the agent writes a `knowledge/concepts/<topic>.md`
   article (facts + rationale) or a `.claude/rules/<name>.md` constraint (mechanical / always-or-never,
   only for patterns stable 6+ months), and updates `knowledge/index.md`. The now-promoted (or
   long-absorbed) raw lines are **pruned** from MEMORY.md — that's how it stays under its caps.

Promotion is the **agent-driven audit ritual** — not automatic detection, not manual editing. The
agent has full context at session close; the agent does the writing; the user only confirms.
3× repetition makes a CANDIDATE, not a rule.

### Why no automation for 3× detection?

Earlier drafts considered an `experiences/` staging layer plus a `promote-patterns.py` background
script to auto-detect 3× repetitions. Killed because:

1. **Cross-session detection is unreliable.** Without a persistent background process, the agent can't reliably match semantics across session boundaries.
2. **The automation solved a hypothetical problem.** After one day the staging scaffold had zero entries.
3. **The ritual is better.** `/close-session` runs the agent-with-full-context at session close. Cross-session patterns get noticed WITH intent, not via fragile signature matching.

The kill reduced complexity + restored the «user only talks» invariant that an automated background detector would have threatened.

## Why the chronicle layer rotted (and where it lives now)

v4 shipped two chronicle-shaped defaults: a per-day journal (`daily/YYYY-MM-DD.md`, written by
`/close-day`) and a single rolling "where we left off" file, the next-session-prompt (NSP,
`context/next-session-prompt.md`). Both were the parts that **silently rotted** in long-running
production use:

- **Days went unclosed.** `/close-day` had to be run every day to keep the journal complete; on
  busy days people skipped it (the docs even said that was fine), so the record grew holes.
- **The NSP froze while still LOOKING authoritative.** Because it was ONE file overwritten in
  place, a stale NSP is indistinguishable from a fresh one — it always looks like "today's plan".
  One production instance carried phantom "open" items for **35 days** before anyone noticed.

The failure mode is the same in both: a stale artifact that looks current. **v5 replaces both with
per-session handoffs.** One immutable note per closed session, `<topic>-YYYY-MM-DD.md`, and the hook
always injects the NEWEST one — so a note that states its own date can't pretend to be today's. There
is no rolling file to freeze, and no daily ritual to skip.

**The daily-journal layer is not gone — it's opt-in.** Some users genuinely want a day-by-day work
diary, and `/close-day` can backfill missed days from git history. It now lives in
`.kit/advanced/close-day-layer/` (the `/close-day` skill + the `daily/` templates + the retired NSP
template kept for reference). One `cp` re-enables it, and it composes with the v5 core: `/close-day`
writes the journal, `/close-session` still owns the audit + handoff. See that folder's README.

## The audit ritual (mechanics of /close-session)

```
User types: /close-session
    │
    ▼
Step 1 — Capture: agent appends this session's new patterns to MEMORY.md
         as date-tagged one-liners
    │
    ▼
Step 2 — Audit: agent reads MEMORY.md's date-tagged entries + existing
         knowledge/concepts/*.md + .claude/rules/*.md, and asks:
           which patterns appeared on 3+ distinct dates?
           which deserve a concept article or a hard rule?
    │
    ▼
Agent surfaces 0-4 candidates to the user verbally:
  "noticed Y on three different dates this week — codify as a rule?"
  "concept X already exists — update it with today's observation?"
  "this pattern contradicts rule Z — has something changed?"
    │
    ▼
User responds verbally:
  "yes" → agent writes the patch (article / rule / update) and prunes the raw lines
  "no" / "not now" → agent acknowledges, doesn't write
  "show again" → agent shows the proposed patch text
    │
    ▼
Step 3 — Refresh: agent REPLACES the MEMORY.md header with fresh current-state lines
    │
    ▼
Step 4 — Handoff: agent copies HANDOFF-TEMPLATE.md → context/handoffs/<topic>-YYYY-MM-DD.md
         and fills its five sections. The next session opens with this note.
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

- **session-start.py** — on every new Claude session, injects (in priority order) the
  memory-discipline nudges that fire, session stats, the newest handoff, and the knowledge index
- **protect-tests.sh** — PreToolUse(Edit|Write) guard for `tests/fixtures/canonical/` (if your project adds them)
- **pre-compact.sh** — before context compaction, blocks until MEMORY.md is BOTH fresh AND under its line cap (a fresh-but-oversized file used to slip through)
- **periodic-save.sh** — every ~50 exchanges, prompts the agent to save new patterns
- **session-end.sh** — SessionEnd timestamp logging

A sixth script sits beside them: **stale-refs.py** (`.claude/memory/scripts/`), which the
session-start hook runs to check that file paths mentioned in CLAUDE.md + MEMORY.md still exist on
disk — a stale belief that looks current is the #1 memory failure, and this catches the file-path
class of it deterministically.

Hooks are invisible to the user. They just make sure state survives.

## Naming discipline

File names are in English for canonical compatibility. Agent references them in Russian conversation naturally. No need to teach the user English filenames.

Per-project folders can use any naming: `projects/client-nestle/`, `projects/nachalo/`, `projects/mvp-launch/` — whatever the user prefers.

## What's NOT in the architecture (by design)

- **`context/next-session-prompt.md` (the NSP)** — the single rolling "where we left off" file;
  retired in v5 because a stale copy looks identical to a fresh one (the 35-day phantom case).
  Replaced by per-session handoffs. The template is kept for reference in `.kit/advanced/close-day-layer/`.
- **`daily/` + `/close-day` in the default surface** — the per-day journal moved to opt-in
  `.kit/advanced/close-day-layer/` in v5. It composes with the core if you want a work diary.
- **`experiences/`** — over-engineered staging layer, deleted in v4.
- **`promote-patterns.py`** — background 3×-detection script, replaced by the audit ritual.
- **`playbooks/` + role-guidance reference skills** — draft-era layers for role wisdom; killed
  because generic seeds were noise. The pattern still works if you add your own per-project.
- **`/memory-audit` + `/memory-compile` operators** — removed in v4; the audit ritual writes
  `knowledge/concepts/` articles directly, on user "yes".
- **`/memory-lint`, `/memory-query`, `/memory-usage` in the default surface** — moved to opt-in
  `.kit/advanced/`. Default operators are just `/close-session` + `/tour`; the rest are power-user
  tooling you copy in when your knowledge base has grown.
- **`knowledge/connections/` + `knowledge/meetings/`** — extra subdirs that nobody filled; collapsed into single `knowledge/concepts/`.
- **Custom trigger keyword tables in CLAUDE.md** — Claude auto-invokes skills from their `description`; no hand-maintained routing.
- **`wisdom/`**, **`lessons/`** — synonyms of existing layers, kept out.
- **Automatic rule generation** — rules are user-approved only, never auto-written.

### Adding role-guidance yourself (advanced)

If you want the role-guidance pattern back for your project, create skills under `.claude/skills/<role>-guidance/SKILL.md` with `user-invocable: false` and a keyword-rich `description`. Claude will auto-invoke them on description match. The kit doesn't seed templates — what works for content marketing is wrong for SaaS dev is wrong for editorial work, so a generic seed is noise.

## Related

- `README.md` — human-facing value prop (project root)
- `CLAUDE.md` — agent-facing session workflow (project root)
- `.claude/skills/close-session/SKILL.md` — the full end-of-session ritual
- `.kit/advanced/README.md` — opt-in layers (power commands + the daily-chronicle layer)
- `.kit/CHANGELOG.md` — version history including the v5.0 lean-core pivot
- Anthropic docs: `code.claude.com/docs/en/skills`, `code.claude.com/docs/en/memory`, `code.claude.com/docs/en/best-practices`
