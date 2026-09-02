# Memory Kit v6 — Architecture

> Full architecture with rationale. Read after the plugin's `context/identity.md` for depth.

## The core invariant

**User only talks. Agent captures, proposes, writes.** This is the one rule that makes everything else consistent.

If an architectural decision violates this invariant (e.g., «user should periodically review memory files and edit them»), it's wrong by definition.

## Layer map (what lives where)

v6 ships as ONE Claude Code plugin. The plugin owns behaviour (hooks, skills, agents, templates);
your repository owns state (memory, handoffs, knowledge). Nothing is copied into `.claude/` except
the state you agreed to in `/memory-kit:setup`, and there is no `CLAUDE.md` block to paste — a
plugin cannot ship `CLAUDE.md` or `.claude/rules/`, so the working agreement is injected by the
SessionStart hook and versioned with the plugin. Every layer maps to a native Claude Code concept
documented at `code.claude.com/docs`.

```
╔══════════════════════════════════════════════════════════════╗
║  SESSION ENTRY (injected by the plugin's session-start.py)   ║
║  ──────────────────────────────────────────────────────────  ║
║  1. context/identity.md — the working agreement (plugin)     ║
║  2. Memory-discipline nudges — ONLY when they fire           ║
║       (the three MEMORY.md caps + stale file references)     ║
║  3. Session stats — MEMORY.md size vs caps,                  ║
║       projects/experiments overview, git state               ║
║  4. .claude/memory/MEMORY.md — THE HOT CACHE ITSELF          ║
║  5. context/handoffs/<newest>.md — "where we left off"       ║
║  6. knowledge/index.md — the catalog of deep memory          ║
║                                                              ║
║  Profiles: startup/clear/fork → all six · compact → 1 + 4    ║
║  plus a one-line pointer to the newest handoff               ║
║  (what compaction drops) · resume → 2 + 3 only               ║
╠══════════════════════════════════════════════════════════════╣
║  ALSO IN CONTEXT (loaded by Claude Code itself)              ║
║  ──────────────────────────────────────────────────────────  ║
║  CLAUDE.md                  — YOUR project's own, if any     ║
║  .claude/rules/*.md         — unconditional or `paths:`-     ║
║                               scoped project rules           ║
║  (+ every skill's `description` — body loads on invoke)      ║
╠══════════════════════════════════════════════════════════════╣
║  ON-TRIGGER (loaded when relevant)                           ║
║  ──────────────────────────────────────────────────────────  ║
║  skills/<task>/SKILL.md         — plugin skills, body loads  ║
║                                   only when invoked          ║
║  reference/*.md                 — depth, read on demand      ║
║  knowledge/concepts/*.md        — deep reference articles    ║
║  projects/<active>/              — that project's OWN docs:  ║
║      README.md (the map) · BACKLOG.md · plans/ (specs) ·     ║
║      research/ · decisions-log.md · review-findings.md ·     ║
║      qa/ · materials/ — loaded when the project is named     ║
╠══════════════════════════════════════════════════════════════╣
║  HANDOFF HISTORY (grep-on-demand, not auto-loaded wholesale) ║
║  ──────────────────────────────────────────────────────────  ║
║  context/handoffs/<topic>-YYYY-MM-DD.md                      ║
║      — one immutable note per closed session; only the       ║
║        NEWEST is injected at session entry                   ║
╠══════════════════════════════════════════════════════════════╣
║  OPERATORS (invoked by user speech)                          ║
║  ──────────────────────────────────────────────────────────  ║
║  all namespaced /memory-kit:<name>                           ║
║  close-session    end-of-session AUDIT ritual + handoff      ║
║  memory-audit     cap-trip surgery on the hot cache          ║
║  system-audit     periodic 7-lens sweep of the whole system  ║
║  setup · tour     adopt the kit here · walkthrough           ║
║  session-review   adversarial close loop                     ║
║  second-opinion   cross-check before commit                  ║
║  qa-sweep         multi-lens QA of the running app           ║
╚══════════════════════════════════════════════════════════════╝
```

![](../.github/assets/03-where-memory-lives.png)

## What each layer is FOR (and is NOT)

### context/identity.md (in the plugin) — the working agreement
**Is:** how the agent works with memory here — the two invariants, the layer map, the caps, what
needs a "yes", and (since 6.1.1) the one place that names the operators and the `reference/`
directory, so depth that costs nothing until opened can actually be found. Injected at session
start and after compaction; versioned with the plugin.
**Is not:** your project's `CLAUDE.md`. That one is yours: stack, conventions, domain. The kit
never writes to it.

### .claude/memory/MEMORY.md — hot cache
**Is:** a current-state header (2-3 sentences, replaced every close) followed by date-tagged
one-liners captured during sessions — observations worth keeping, each with the date it was
seen, so that repetition on 3+ distinct dates becomes visible. Short strings. Cross-session
accumulator. Held under three caps (below).
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

### skills/<task>/SKILL.md (in the plugin) — task skills
**Is:** a repeatable workflow invoked as `/memory-kit:<task>`. Only the `description` of each skill
sits in context; the body loads on invoke — which is why the builder's layers (session review,
second opinion, QA sweep, system audit) can ship by default without costing a memory-only user
anything.
**Is not:** knowledge or rules. If it's "do these steps" → task skill. If it's "always X" → rule. If it's "what is X" → concept.

### knowledge/concepts/*.md — deep reference
**Is:** facts + rationale, topic-oriented. "Our typography scale: 43 paired sub-tokens. Sizes, line heights, weights. Reasoning per level."
**Is not:** workflow methodology (that's a task skill or rule). Not date-tagged short notes (that's MEMORY.md).

### projects/<name>/ — the work's own documents
**Is:** everything the work itself produces for ONE client or product, and the only layer that is
not memory. `README.md` — what the project is plus **the map of where its documents live**, which
is the SSOT that answers "where does a plan go". `BACKLOG.md` — tasks and their honest status.
`plans/YYYY-MM-DD-<slug>.md` — the specs an `executor` builds to (`SPEC-TEMPLATE.md`), written
BEFORE any fan-out and integrator-owned. `research/<topic>-YYYY-MM-DD/` — what a `recon` sweep or
an acceptance run produced, dated because outside facts rot. `decisions-log.md` — the numbered
ledger. `review-findings.md` — the finding-class registry the promotion rule counts. `qa/` — the
QA protocol and its run records. `materials/` — briefs, PDFs, brand books the user drops in.

A single-product code repository has exactly ONE of these folders, named after the product. The
per-project scoping is not decoration: a ledger's `D-00N` ids, a findings class count and a QA
protocol's environment each describe one product, and merging two products into one file makes
all three lie.

**Is not:** memory (that's the four shared layers — a dated pattern never lands here, and a spec
never lands in `MEMORY.md`). Not shared knowledge: something true across every client is a
`knowledge/concepts/` article. Not a sandbox for prototypes (that's `experiments/`). Not
scaffolded upfront — every path except `README.md` and `BACKLOG.md` appears when something is
actually written into it.

**When the repository already has a `docs/`:** it stays exactly where it is. The README's map
table repoints to it, and the kit migrates nothing — a working layout outranks a default.

### experiments/<name>-YYYYMMDD/ — sandbox
**Is:** R&D folder for hypotheses, prototypes, throwaway research. `EXPERIMENT.md` (hypothesis + result), optional code, notes, screenshots. Date in folder name.
**Is not:** real client work (that's `projects/`). Not a long-term home — closed experiments are distilled into `knowledge/concepts/` (lessons) and `projects/` (code), then deleted (git history remembers).

Why a separate layer? Different lifecycle (days, not indefinite), different quality bar (rough OK), different relationship to the `/close-session` audit (no direct promotion to rules — distill first, then close). Full spec: the plugin's `templates/workspace/experiments-README.md`, which `/memory-kit:setup` copies in if you want the sandbox layer.

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

![](../.github/assets/04-promotion-agent.png)

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

**v6 retires the daily-journal layer entirely.** v5 demoted it to opt-in and, in a year of real
use across many cloned instances, nobody enabled it: `/memory-kit:close-session` covers the same
ground per session and cannot go stale unnoticed. The code stays in git history for anyone who
wants it back.

## The audit ritual (mechanics of /close-session)

![](../.github/assets/02-session-loop-agent.png)

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

![](../.github/assets/05-multi-project-layer.png)

![](../.github/assets/08-one-operator-five-hosts.png)

One agent, many projects. The split is not "big things vs small things" — it is **memory vs
paperwork**. What the agent LEARNED is shared across every project; what the work PRODUCED
belongs to one of them.

```
Shared (memory — loaded every session):
  CLAUDE.md, .claude/memory/MEMORY.md, context/handoffs/, knowledge/, .claude/rules/
  context/audits/            (audits of the agent SYSTEM — not of any one project)

Project-scoped (the work's own documents — loaded when the project is named):
  projects/<active>/README.md          the map: where this project's documents live
  projects/<active>/BACKLOG.md         tasks + honest status
  projects/<active>/plans/             specs an executor builds to (pre-registered acceptance)
  projects/<active>/research/          dated recon output + acceptance evidence
  projects/<active>/decisions-log.md   the numbered ledger
  projects/<active>/review-findings.md the finding-class registry
  projects/<active>/qa/                QA protocol + run records
  projects/<active>/materials/         briefs, PDFs, brand books
```

Why per-project and not one shared set: a decision ledger numbers `D-001…` for one product, the
findings registry promotes a class on its **third** occurrence, and a QA protocol names one app's
URLs and accounts. Interleave two clients into any of those three and the ids collide, the count
becomes meaningless, and a lens gets pointed at the wrong app. A single-product repository still
gets one project folder — the shape does not change, only the count.

Switch command (in conversation): "we're working on client-a" → agent unloads client-b materials,
loads client-a. For project-scoped rules, use `paths: [projects/client-a/**]` frontmatter on the
rule file.

**Adopting a repository that already has a `docs/`:** nothing moves. `projects/<name>/README.md`
maps each document class to the path the repo already uses, and that map is what the agent reads
before writing a plan. Defaults are a default; a working layout outranks them.

## Hooks (automatic, no user action)

![](../.github/assets/06-hooks-skills.png)

Four hooks, declared in the plugin's `hooks/hooks.json` — nothing to wire in your settings:

- **session-start.py** — injects the working agreement, the nudges that fire, session stats, THE
  HOT CACHE ITSELF, the newest handoff and the knowledge index, with a profile per `source`
  (see the layer map). In a repository that never ran `/memory-kit:setup` it injects one pointer
  line and writes nothing — a plugin can be installed user-wide and must not scaffold uninvited.
- **protect-tests.py** — PreToolUse(Edit|Write): asks before an EXISTING test file is edited
  ("a failing test means the code is wrong"), always allows a new test and any test this session
  created (the red→green loop), and honours `CMK_ALLOW_TEST_EDITS=1`.
- **pre-compact.sh** — blocks compaction until MEMORY.md is BOTH fresh AND inside all three caps.
- **session-end.sh** — SessionEnd timestamp logging.

Beside them sits **stale-refs.py** (`hooks/lib/`), which the session-start hook runs to check that
file paths mentioned in CLAUDE.md + MEMORY.md still exist on disk — a stale belief that looks
current is the #1 memory failure, and this catches the file-path class of it deterministically.

**Retired in v6: `periodic-save.sh`.** A Stop hook fires at the end of EVERY turn, and it parsed
the whole transcript each time to count exchanges — a cost that grows with the session, paid on
every turn, to re-state what PreCompact already enforces at the moment it matters.

Hooks are invisible to the user. They just make sure state survives.

**What the injection costs** (measured 2026-09-02 by running `session-start.py` and counting
characters ÷ 4): a fresh install ~2.3k tokens, a working 6 KB cache with a handoff ~3.5k, and a
hard ceiling of ~12k when the cache sits at all three caps and the handoff at its 6 KB inject
cap. Skill and agent descriptions add ~1.8k on every host that loads them. The caps are what
make the ceiling a number instead of a trend. For comparison, Claude Code's own auto memory
loads the first 200 lines or 25 KB of its index at every start (its docs, read 2026-09-02).

## Platform tiers (beyond Claude Code)

The kit is authored as a Claude Code plugin, but the STATE it manages is plain markdown in your
repository — readable by any agent. v6.3.0 names the three delivery tiers instead of pretending
every host is equal:

| Tier | Hosts | What runs |
|---|---|---|
| **T1 — enforcement** | Claude Code · OpenCode (via the shipped `.opencode/plugins/memory-kit.js` shim, verified 2026-08-31) | Guarantees, not requests — but not the same three on both hosts. **Claude Code:** injection at session start, the PreCompact block, the test guard. **OpenCode:** memory rides `experimental.chat.system.transform` into EVERY model call, so compaction cannot drop it (the block is unnecessary rather than missing); no test guard yet; `experimental.session.compacting` appends a save-state instruction. |
| **T2 — protocol** | Codex and GitHub Copilot CLI (both verified 2026-08-31), Cursor (verified 2026-08-31 — its CLI even executes the SessionStart hook, giving T1-grade wake-up; the other three hooks unprobed), Claude Cowork (documented-only 2026-09-02: skills load, plugin hooks do not fire — `specs/cowork.md`) — anything that auto-loads `AGENTS.md` or `CLAUDE.md` | `/memory-kit:setup` appends a marker-fenced block (`templates/workspace/AGENTS-MEMORY-PROTOCOL.md`, <2.1 KB) telling the agent to do by hand what the hooks do mechanically: read memory first, respect the caps, save before compaction, close with the ritual. Advisory — an agent can forget an instruction; it cannot ignore a hook. |
| **T3 — plain files** | anything else, including CI | the memory files themselves need no runtime: markdown, git-versioned, one `grep` away. |

Codex empirics (see `specs/codex.md` for the probes): it installs the kit from the NATIVE
manifests — the nested `plugins/memory-kit` marketplace source resolves, all 8 skills appear in
a live session namespaced `memory-kit:<name>` — and it parses `hooks.json` but does NOT execute
SessionStart. "Wakes up already knowing" does not exist there; the protocol block is the honest
replacement. Per-host truth, every claim labeled `verified` / `documented-only` /
`manual-check-needed`, lives in `docs/specs/`.

Deliberately NOT adopted from the compound-engineering-plugin pattern (the repo that runs 33
skills on 14 hosts, studied 2026-08-31): a converter pipeline and a root-native layout
migration — either waits until a real host demonstrably needs it. `context/identity.md` remains
the SSOT the protocol block is distilled from; a change to one touches the other in the same
commit.

## Naming discipline

File names are in English for canonical compatibility. Agent references them in Russian conversation naturally. No need to teach the user English filenames.

Per-project folders can use any naming: `projects/client-nestle/`, `projects/nachalo/`, `projects/mvp-launch/` — whatever the user prefers.

## What's NOT in the architecture (by design)

- **`context/next-session-prompt.md` (the NSP)** — the single rolling "where we left off" file;
  retired in v5 because a stale copy looks identical to a fresh one (the 35-day phantom case).
  Replaced by per-session handoffs.
- **`daily/` + `/close-day`** — the per-day journal: demoted to opt-in in v5, retired in v6.
  Nobody enabled it, and a chronicle with holes is worse than no chronicle.
- **`experiences/`** — over-engineered staging layer, deleted in v4.
- **`promote-patterns.py`** — background 3×-detection script, replaced by the audit ritual.
- **`playbooks/` + role-guidance reference skills** — draft-era layers for role wisdom; killed
  because generic seeds were noise. The pattern still works if you add your own per-project.
- **`/memory-compile`** — auto-folding daily logs was unreliable; the audit ritual writes
  `knowledge/concepts/` articles directly, on user "yes". (`/memory-query` went the same way in
  v5.1 — asking the agent in conversation covers it.)
- **A separate "advanced" distribution surface** — v5 parked the power tooling in `.kit/advanced/`
  behind `cp` instructions, and v6.0 briefly split the kit into three plugins. Both were paying a
  distribution cost to save a memory-only user a handful of skill descriptions, since skill bodies
  load only on invoke. One plugin, everything inside; the only always-on optional piece is the
  ~20-line `orchestration.md` rule that `/memory-kit:setup` offers.
- **`knowledge/connections/` + `knowledge/meetings/`** — extra subdirs that nobody filled; collapsed into single `knowledge/concepts/`.
- **Custom trigger keyword tables in CLAUDE.md** — Claude auto-invokes skills from their `description`; no hand-maintained routing.
- **`wisdom/`**, **`lessons/`** — synonyms of existing layers, kept out.
- **Automatic rule generation** — rules are user-approved only, never auto-written.

### Adding role-guidance yourself (advanced)

If you want the role-guidance pattern back for your project, create skills under `.claude/skills/<role>-guidance/SKILL.md` with `user-invocable: false` and a keyword-rich `description`. Claude will auto-invoke them on description match. The kit doesn't seed templates — what works for content marketing is wrong for SaaS dev is wrong for editorial work, so a generic seed is noise.

## Related

- `README.md` — human-facing value prop (repo root)
- `plugins/memory-kit/context/identity.md` — what the agent is told every session
- `plugins/memory-kit/skills/close-session/SKILL.md` — the full end-of-session ritual
- `plugins/memory-kit/reference/` — depth: fact-check, parallel development, doc governance,
  decisions log, review loop, the QA protocol template
- `docs/specs/` — per-host capability specs (what each agent platform honours, empirically)
- `docs/CHANGELOG.md` — version history including the v6.0 plugin pivot
- Anthropic docs: `code.claude.com/docs/en/skills`, `code.claude.com/docs/en/memory`, `code.claude.com/docs/en/best-practices`
