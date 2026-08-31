# Changelog

All notable changes to Memory Kit are documented here. Breaking changes marked **BREAKING**.

<a id="v640"></a>

## [6.4.0] — 2026-08-31 — The rebrand: agent-memory-kit, and a README that breathes

The kit is verifiably multi-host now, and both the name and the front page still said
otherwise. Repo renamed `claude-memory-kit` → **`agent-memory-kit`** (supersedes D3; GitHub
redirects preserve every existing link; the plugin id `memory-kit@memory-kit` is untouched, so
no install breaks — done deliberately BEFORE the Cursor marketplace submission, so no external
catalog ever carries the old slug).

README rewritten around the new lead — **"One memory for every coding agent"** — cut from
~2,700 to ~1,100 words: the hosts matrix moved above the fold, the Before/After table dropped
(per D7), FAQ 9 → 4, and two stale v5 claims fixed while at it (the "~50-message autosave"
and the "hook recreates MEMORY.md" answers described retired behaviour). Displaced diagrams
re-homed to `docs/ARCHITECTURE.md` and the plugin README so the no-orphan CI check keeps
telling the truth. `displayName` → "Memory Kit"; manifest descriptions de-Claude-ified.

Full asset sweep followed (every diagram opened and read — the ASSETS.md rule): five
regenerated with new filenames (camo cache-bust) — the og-banner (old repo name + "The OS
layer for Claude Code" headline), `02`/`04` ("Claude" as the actor → "the agent"), `08`
("three lines in Claude Code" footer → "one install — Claude Code, Cursor or Codex"), and
`09`, whose footer still pointed at `docs/qa/README.md` two versions after v6.2.0 moved the
QA protocol to `projects/<name>/qa/README.md`. `03`/`05`/`06`/`07` verified host-neutral and
kept. Details per asset: `docs/ASSETS.md`.

<a id="v631"></a>

## [6.3.1] — 2026-08-31 — Cursor marketplace manifests

Packaging for the central Cursor Marketplace submission. Cursor's own multi-plugin format maps
1:1 onto our layout — root `.cursor-plugin/marketplace.json` with `source: plugins/memory-kit`,
plus `plugins/memory-kit/.cursor-plugin/plugin.json` — so nothing moves. Both new manifests are
covered by the CI version-agreement check (`tools/check-repo.py`). The marketplace itself is
curated ("we work with a small group of trusted partners" — their security page), submission is
a sign-in application at cursor.com/marketplace/publish with manual review and no published
SLA; the mechanics and the submission checklist live in `docs/specs/cursor.md`. Note these
manifests are NOT needed for the already-verified git-URL install path — they exist only for
the central listing.

<a id="v630"></a>

## [6.3.0] — 2026-08-31 — Platform tiers: the kit beyond Claude Code

Studied [everyinc/compound-engineering-plugin](https://github.com/everyinc/compound-engineering-plugin)
— 33 skills on 14 agent hosts from one Claude-format source — and adopted the parts of its
pattern that survive contact with a hooks-first kit. The honest difference: their product is
prompt-skills (trivially portable); ours is hook enforcement, which most hosts cannot run. So
instead of pretending parity, the kit now names its **three delivery tiers**: T1 enforcement
(Claude Code hooks — injection, PreCompact block, test guard), T2 protocol (an auto-loaded
`AGENTS.md` block instructs the agent to do by hand what the hooks do mechanically), T3 plain
files (the memory state is markdown any agent can read). Hooks are byte-identical in this
release.

### Added

- **`templates/workspace/AGENTS-MEMORY-PROTOCOL.md`** — the T2 core: a <2.1 KB, marker-fenced
  protocol block (session-start reads, the two invariants, the three caps, pre-compact save,
  test rule, close ritual) distilled from `context/identity.md`. Upgrades REPLACE the marked
  block, never stack a second copy.
- **`docs/specs/`** — per-host capability docs in the compound-engineering style: dated
  "Last verified", every claim labeled `verified` / `documented-only` / `manual-check-needed`,
  degradation stated instead of hidden. Ships with `claude-code.md` (T1 baseline),
  `codex.md` (verified), `cursor.md` (manual checklist pending), `agents-md.md` (the T2
  delivery convention itself).
- **`/memory-kit:setup`** gains the "other agents also work in this repo?" offer (append the
  protocol block to `AGENTS.md`, diff-first, marker-replace on upgrade) and a cross-host note:
  under a non-Claude host `${CLAUDE_PLUGIN_ROOT}` doesn't expand — resolve plugin paths
  relative to the SKILL.md file itself and skip the Claude-only steps out loud.

### Verified (2026-08-31, codex-cli 0.151.0, live `codex exec` probes)

- **Codex installs the kit from the NATIVE manifests.** `codex plugin marketplace add
  awrshift/agent-memory-kit` reads `.claude-plugin/marketplace.json` and resolves the nested
  `plugins/memory-kit` source — no adapter manifest, no root-native layout migration needed.
- **All 8 skills are visible in a live Codex session**, namespaced `memory-kit:<name>`.
- **The full T2 chain passed a canary probe**: `AGENTS.md` auto-loads, its instruction is
  followed, `MEMORY.md` is read and its content surfaced.
- **Codex parses `hooks.json` but does not run SessionStart** — no injection, no PreCompact
  block there. Tier 2 for Codex is measured, not assumed.

### Verified (2026-08-31, cursor-agent 2026.08.25, headless probes)

- **Cursor indexes the kit's marketplace from a plain git URL** (`cursor-agent plugin
  marketplace add …`) — nested source resolves; no central-marketplace publication required.
- **`--plugin-dir` loads the full plugin: all 8 skills visible.** `.cursor/skills/` also
  accepts Claude-format SKILL.md dirs as-is.
- **Cursor CLI executes the SessionStart hook and honours `additionalContext`** — the memory
  canary and an identity.md-only phrase were in context with the plugin loaded and absent
  without it. "Wakes up already knowing" works on Cursor; PreCompact/PreToolUse remain
  unprobed there.
- **The `AGENTS.md` canary chain passed on Cursor too** — auto-loaded, instruction followed,
  `MEMORY.md` read.

### Changed

- `docs/ARCHITECTURE.md` — new "Platform tiers" section; root README and the plugin README now
  state what each tier keeps and loses.
- Deleted untracked `scripts/__pycache__/` litter from the plugin tree — a local Codex install
  was faithfully copying it into its plugin cache.

<a id="v620"></a>

## [6.2.0] — 2026-08-27 — The project layer: where the work's own documents live

The kit was multi-project in its MEMORY and single-project in its PAPERWORK. Every artifact the
builder's layers produce had a root-level address — `docs/qa/README.md`, `context/review-findings.md`,
`docs/decisions-log.md` — so a workspace with five clients got one QA protocol, one findings
registry and one decision ledger for all of them. And the most load-bearing artifact of the whole
orchestration model, the spec an `executor` builds to, had no address at all: it lived in a prompt,
which meant it could not be re-read at merge, diffed against what was built, or found the next day.

### Added

- **`projects/<name>/` is now the documented home of the work's own documents**, and the first
  thing in it is `README.md` — a map table of where this project's tasks, specs, research,
  decisions, findings and QA records live. That table is the SSOT answering "where does a plan
  go"; the default paths are a default, not a law.
- **`templates/workspace/project/`** — three new templates: `README-TEMPLATE.md` (the map),
  `SPEC-TEMPLATE.md` (goal · non-goals · **pre-registered** acceptance · gates · slices ·
  registered deviations — the contract an executor builds to), and a working `BACKLOG-TEMPLATE.md`.
- **`reference/project-extensions.md`** — the decision table for when a repeated workflow earns a
  project skill, hook, agent or rule, what each costs when idle, and the three questions to ask
  before adding any of them. Previously the kit audited these layers (`system-audit` lens 4) while
  never saying how to build one.

### Changed

- **The spec is a file, not a prompt.** `parallel-development.md` gains Level 0: the contract is
  written at `projects/<name>/plans/YYYY-MM-DD-<slug>.md` before any fan-out, and executor prompts
  POINT at that path. `agents/executor.md` now says to read the spec file in full, treats its
  Non-goals as binding, and forbids editing it — the integrator owns it and adjudicates deviations.
- **The agentic artifacts got project addressing:** the QA protocol and run records
  (`docs/qa/` → `projects/<name>/qa/`), the findings registry (`context/review-findings.md` →
  `projects/<name>/review-findings.md`), the decision ledger (`docs/decisions-log.md` →
  `projects/<name>/decisions-log.md`). `context/audits/` stays at the root — a system audit is
  about the agent system, not about one client.
- **`recon` names what is worth filing**, and the integrator files it under
  `projects/<name>/research/<topic>-YYYY-MM-DD/` — dated, because an outside fact older than a week
  is a hypothesis again.
- **`/memory-kit:setup` gains Step 1b** and drops the rule that said not to create `projects/` in a
  code repository. That rule is why specs, backlogs and research had nowhere to go in exactly the
  repos that run executors. A single-product repo now gets one project folder, named after the
  product. Only `README.md` and `BACKLOG.md` are scaffolded; every other path appears on first use.
- **A repository that already has a `docs/` keeps it.** Setup maps it in the project README and
  migrates nothing.
- **`context/identity.md`** (injected every session) now draws the line explicitly: four memory
  layers, and `projects/<name>/` which is not a fifth — memory is what the agent learned, a project
  folder is what the work produced.
- `templates/workspace/BACKLOG-TEMPLATE.md` → `ONBOARDING-BACKLOG.md`. It was a five-task day-one
  tutorial being handed out as the template for real project backlogs.

### Fixed

- **`docs/ARCHITECTURE.md` still listed `memory-usage` and `memory-lint`** as operators, ten
  days after 6.1.0 removed them (2026-08-17) — the exact drift its own `doc-governance.md` R2
  forbids, and it survived the 6.1.1 release in between.

### Migration

Nothing breaks and nothing moves on its own. Existing repos keep their current paths; when you
next touch one of the relocated files, either move it into the project folder or leave it and
repoint the row in `projects/<name>/README.md`. `/memory-kit:setup` can be re-run safely — it
creates only what is missing — and is the easiest way to get the project README written for you.

<a id="v611"></a>

## [6.1.1] — 2026-08-18 — The depth nobody could find

### Fixed

- **`reference/` was unreachable.** Six documents — `orchestrator-fact-check`, `review-loop`,
  `parallel-development`, `doc-governance`, `decisions-log`, `capability-map-sweep` — were named
  only in the README (not loaded), in `/memory-kit:setup` (only if invoked) and in
  `templates/rules/orchestration.md` (only if the user copied it into `.claude/rules/`). Grepped
  across the skills: every one of them except `qa-PROTOCOL-TEMPLATE` was referenced **zero** times.
  A user who installed the plugin and skipped setup never learned they exist.

  Now `context/identity.md` — the one file injected into every session — names the operators and
  the `reference/` directory, and each document is cited from the skill that needs it:
  `close-session` → `doc-governance` + `decisions-log`; `session-review` → `orchestrator-fact-check`,
  `parallel-development`, `review-loop`; `second-opinion` → `orchestrator-fact-check`;
  `system-audit` lenses 2 and 3 → `doc-governance`, `review-loop`, `parallel-development`;
  the `recon` agent → `capability-map-sweep`.

  The subtraction rule cuts both ways: a layer nobody can reach is decoration, whether it was
  never written or merely never linked.

- **A broken path in `agents/qa.md`** — it pointed at `rules/orchestrator-fact-check.md`, a v5
  location. The file has lived in `reference/` since 6.0.0.

- **`close-session` had no `allowed-tools`.** Now `Read, Write, Edit, Grep, Glob, Bash`. The
  orchestrating skills (`session-review`, `second-opinion`, `qa-sweep`, `system-audit`)
  deliberately keep inheriting the full set: they spawn subagents, and the spawn tool has been
  renamed across Claude Code versions — pinning a list there would break the skill on the version
  that calls it something else. An `allowed-tools` that can silently disable a skill is worse than
  none.

Nothing in a user's repository changes; `/memory-kit:setup` is not required after this upgrade.

<a id="v610"></a>

## [6.1.0] — 2026-08-17 — Two skills nobody ran

### Removed

- **`/memory-kit:memory-lint`.** It linted `[[wikilink]]` hygiene — broken links, orphan pages,
  missing backlinks — for a convention the kit does not actually ship: nothing in the templates
  emits wikilinks. It sat behind a `cp` step from v4.2.0 to v6.0.0 and never produced a report in
  this repository's history. What was load-bearing in it (frontmatter coverage, references that
  no longer resolve) the system-audit collector already gathers generically.

### Changed

- **`/memory-kit:memory-usage` folded into `/memory-kit:system-audit`.** The transcript profiler
  is real signal — it is the only thing that can answer *"did this rule / skill / agent ever
  actually fire?"* — but that question belongs to the audit's layer-telemetry lens, which until
  now described a telemetry table nobody generated. The script moved to
  `skills/system-audit/scripts/usage.py` and the lens invokes it. One fewer skill, one lens that
  can finally be executed instead of aspired to.

The subtraction rule this follows: a layer that has never fired is not "available", it is
decoration. It was written into the audit's own lens 7 before it was applied here.

<a id="v600"></a>

## [6.0.0] — 2026-08-17 — The plugin pivot (and the bug that made it urgent)

**BREAKING (distribution only, not your data).** The kit is no longer a repository you clone and
live inside — it is a Claude Code plugin you install into a repository you already have. Every
memory path is unchanged: `.claude/memory/MEMORY.md`, `context/handoffs/`, `knowledge/concepts/`,
`.claude/rules/`. Nothing in your accumulated memory needs to move.

### Fixed — the hot cache was never actually loaded

Since v3 the kit told the agent that `.claude/memory/MEMORY.md` was "always loaded (hot path)".
It was not. Claude Code auto-loads `CLAUDE.md`, `.claude/rules/` and its OWN auto-memory
directory — never the kit's file. `CLAUDE.md` carried no `@` import of it, and `session-start.py`
only ever read the file to *measure* it. So the ritual wrote, session after session, into a file
the agent saw only if it happened to open it.

The hook now injects the BODY of the cache (budget raised 20k → 48k) and re-injects it after
compaction. The lesson generalizes: **a claim that something is "in context" is verified by
looking at the context, not by reading the code that produced it.**

### Fixed — the permission allowlist that allowed everything

`.claude/settings.json` shipped `Bash(git *)`, `Bash(npm *)`, `Bash(node *)`, `Bash(python3 *)`
in `allow` with an empty `deny` — auto-approving forced pushes, hard resets, and arbitrary
execution via `node -e`. `/memory-kit:setup` now proposes a real rail: `deny` on forced pushes
and secret reads, `ask` on the destructive classes, no blanket interpreter wildcards.
A permission entry is a speed bump for the agent, never a guard on a script.

### Fixed — the test guard broke TDD

`protect-tests.sh` allowed creating a test with Write and then hard-blocked (`exit 2`) every
later Edit of it, so a red→green loop could not run, and there was no escape hatch. Replaced by
`protect-tests.py`: `permissionDecision: "ask"` instead of a refusal, always-allow for a file the
session created, fixtures and data files exempt, and `CMK_ALLOW_TEST_EDITS=1` for a deliberate
test-maintenance session.

### Added

- **`/memory-kit:setup`** — adopts the kit in an existing repo: scaffolds only what's missing,
  asks who owns memory (see below), proposes the permission rails and `.gitignore` lines, and
  offers the ~20-line orchestration rule. Writes nothing before a yes.
- **`/memory-kit:memory-audit`** — the cap-trip surgery, split out of the daily ritual: classify
  every section, propose a move plan as a table, execute atomically on approval. The hook's cap
  nudge now points here. A daily ritual that also has to perform surgery is a ritual people skip.
- **`/memory-kit:system-audit`** — the periodic seven-lens sweep of the whole system (delivery
  reality · knowledge drift · operational layer · layer telemetry "did it ever fire" · tools and
  infra · domain gaps · anti-bloat subtraction), with a deterministic collector script and the
  rule that every finding carries something you touched with your own hands.
- **The auto-memory decision.** Claude Code now ships its own auto memory (on by default,
  `~/.claude/projects/<project>/memory/`, loaded every session). Running it alongside the kit
  means two writers and two truths — so setup makes the choice explicit: the kit owns memory
  (`autoMemoryEnabled: false`), or native owns capture and the kit keeps the ritual
  (`autoMemoryDirectory` pointed at the repo).
- **SessionStart profiles** by `source`: startup/clear/fork get the full payload, `compact` gets
  exactly what compaction drops (the working agreement + the cache), `resume` gets only the
  nudges and stats. v5 fired everything on all five, and counted every one as a new "session".
- **State pruning** — per-session bookkeeping in `.claude/state/` older than 30 days is deleted.
  It accumulated forever in v5.

### Changed

- **One plugin, not three.** The first cut of v6 split core / orchestration / QA into three
  installable plugins. Reverted before release: skill bodies load only on invoke, so the whole
  split was paying a distribution cost to save a memory-only user a handful of description lines.
- **The working agreement ships in the plugin** (`context/identity.md`, injected every session)
  instead of a `CLAUDE.md` you maintain. A plugin cannot ship `CLAUDE.md` or `.claude/rules/`,
  and that constraint turned out to be the better design — the agreement is versioned with the
  plugin and updates with it.
- **The rule template is 25 lines, not 40+**, and leads with `paths:`. Rules without `paths:`
  load into context at every session start at CLAUDE.md priority — the old template's review
  history and cross-links taught exactly the habit that makes an always-loaded layer expensive.
- All skills are namespaced `/memory-kit:<name>` and carry real frontmatter (`description`,
  `allowed-tools`, `model` where it matters).
- Kit docs moved `.kit/` → `docs/`; `VERSION` sits at the repo root.

### Removed

- **`periodic-save.sh`** — a Stop hook fires at the end of every turn and this one parsed the
  entire transcript each time to count exchanges. The cost grows with the session, is paid every
  turn, and re-states what PreCompact already enforces at the moment it matters.
- **The daily-chronicle layer (`/close-day`, `daily/`)** — demoted to opt-in in v5 because it
  silently rotted when days were skipped; in practice nobody enabled it. `/memory-kit:close-session`
  covers the same ground per session and cannot go stale unnoticed. Still in git history.
- **`.kit/advanced/` as a distribution surface** — everything it held is either in the plugin or
  retired. No more `cp` instructions.
- The repo-root `SKILL.md` and workspace scaffolding (`projects/`, `experiments/`, `knowledge/`,
  `context/`) — this repository is the marketplace now; your workspace is yours.

### Migration from v5

1. Remove the copies the plugin replaces: `.claude/hooks/`, `.claude/skills/close-session`,
   `.claude/skills/tour`, `.claude/memory/scripts/`, and the kit's hook block in
   `.claude/settings.json`. **Keep** `.claude/memory/MEMORY.md`, `context/handoffs/`,
   `knowledge/`, `.claude/rules/` and your own `CLAUDE.md`.
2. `/plugin marketplace add awrshift/claude-memory-kit` → `/plugin install memory-kit@memory-kit`.
3. `/memory-kit:setup` — it detects what already exists and only fills gaps.
4. Run `/context` and confirm the hot cache is really there. That is the check v5 never made.

## [5.2.0] — 2026-07-18 — The QA layer + the self-improving review loop

The maintainers' agent-QA practice, generalized: agents now probe the RUNNING product from the
user's side, and the review process learns from its own confirmed findings. Everything here was
battle-tested first (four calibrated QA sweeps including a seeded-defect recall run, a dozen
registry rows, and one rule promotion in the first two days of production use).

### Added

- **QA layer** (`.kit/advanced/qa-layer/`, opt-in; requires the orchestration layer):
  - `agents/qa.md` — a lens agent that probes the live app through ONE assigned adversarial
    lens (user-flow · edge-state · honesty · contract · ux-critique) and returns a structured
    findings table with repro steps + evidence. Observation-only by default; mutations happen
    only on a sacrificial seeded account the run brief explicitly grants.
  - `skills/qa-sweep/` — `/qa-sweep`: preflight → pick lenses → spawn qa agents →
    integrator-reproduces every P1/P2 before it becomes a ticket → run record.
  - `PROTOCOL-TEMPLATE.md` — the protocol SSOT to copy into `docs/qa/README.md`: environment +
    two-account policy, the five lens briefs, the findings-format contract, triage, and a
    three-step calibration ladder (per-run precision metrics → a held-out seeded-defect suite
    kept OUTSIDE the repo → brief edits kept only on a measured recall delta). Includes the
    optional Playwright regression-spec loop (`init-agents`), with the healer subordinated to
    "a failing test means the CODE is wrong".
  - `mcp.json.example` — two isolated Playwright MCP servers (`--isolated` +
    `--caps=testing,devtools` + `--test-id-attribute`): concurrent browser lenses with zero
    shared-profile collision, and `browser_verify_*` machine oracles as finding evidence.
- **`rules/review-loop.md`** (orchestration layer) — the two-part feedback loop: (1) every
  nontrivial diff passes an automated code review before the integrator merges (medium effort;
  high on write-path / auth / paid-spend / determinism diffs); (2) every CONFIRMED finding
  appends a class row to `context/review-findings.md`, a class's 3rd recurrence promotes it
  into the cheapest preventing layer (deterministic check → agent-definition line → review-brief
  line → knowledge entry), and promoted rules that stop firing are dropped.
- **`patterns/capability-map-sweep.md`** (orchestration layer) — a recon playbook for the
  "the library already does this" defect class: capability maps built from INSTALLED typings
  (never model memory), a finder pass, integrator adjudication that expects refutations in
  both directions.

### Upgrading an existing orchestration-layer install (works agent-driven)

Point your project's agent at this changelog and say "adopt the v5.2 additions". Mechanically:

1. `cp .kit/advanced/orchestration-layer/rules/review-loop.md .claude/rules/` and create an
   empty `context/review-findings.md` from the table template inside it.
2. Building a user-facing product? Enable the QA layer per
   [`qa-layer/README.md`` (v5.2 path, retired in v6)` — copy the agent + skill, instantiate
   `PROTOCOL-TEMPLATE.md` as `docs/qa/README.md` with your URLs/accounts/journeys, merge
   `mcp.json.example` into `.mcp.json`, gitignore `.claude/qa/`, restart Claude Code.
3. Nothing else changes; existing agents, skills, and rules are untouched.

## [5.1.0] — 2026-07-17 — Full-tree audit: real memory privacy, the orchestration layer, v4-rudiment sweep

A file-by-file audit (four independent review passes: doc/reality cross-check, code review,
portability/privacy, skills consistency) plus one addition: the maintainers' multi-agent
orchestration practice, generalized into an opt-in layer.

### Added

- **Orchestration layer** (`.kit/advanced/orchestration-layer/`, opt-in): three agents —
  `executor` (builds to an already-decided spec in a git worktree, deviations REGISTERED),
  `recon` (read-only fact-gatherer, file:line evidence), `idea-validator` (isolated adversarial
  critic) — two skills — `/session-review` (end-of-session adversarial review loop) and
  `/second-opinion` (Devil's Advocate · Boardroom Debate · Round-Table) — and four rules
  (orchestrator fact-check: "a report is INPUT" · parallel development + worktree isolation ·
  doc governance anti-drift · the lean decisions log). One `cp` set enables it.
- **`MEMORY-TEMPLATE.md` + hook self-heal**: `session-start.py` creates `MEMORY.md` from the
  template on first run, so the privacy change below costs zero setup.

### Changed

- **`MEMORY.md` is now actually gitignored.** The README claimed "handoffs and memory are
  gitignored by default" — only handoffs were. Your hot memory (client names, decisions,
  preferences) would have been committed and pushed with the repo. The FAQ now also states
  plainly that `knowledge/` and rules ARE tracked by design.
- **v4-rudiment sweep**: `_example.md.disabled` (the default rule scaffold) and the opt-in
  `/close-day` skill still referenced the retired `/close-day`-as-default ritual, `daily/` as a
  default folder, and the retired next-session-prompt (NSP) — a user following them would have
  written files nothing reads. All repointed to `/close-session` + handoffs; the close-day
  layer now genuinely composes with the v5 core.
- **`periodic-save.sh` counted tool results as human messages** (both arrive as `role: user`),
  firing the ~50-exchange checkpoint several times too often. Now counts real human turns only.
- **`pre-compact.sh` fresh-gate now checks all three caps** (lines + bytes + longest line), not
  just the line cap — matching the documented three-cap doctrine.
- **`lint.py` wikilink checks fixed**: article existence and backlinks now resolve against
  `knowledge/concepts/` (bare `[[slug]]` convention); previously every real concept would have
  been flagged broken/orphan.
- **`aggregate_usage.py` transcript-dir encoding fixed** for project paths containing dots.
- **`stale-refs.py` cleaned of the maintainers' private-project paths** (leaked hardcoded
  `EXTERNAL_ROOTS` + a foreign docstring); the mechanism stays, the list is now yours to fill.
- **`settings.json` pre-approvals narrowed**: `rm`, `mv`, `chmod` no longer bypass the
  permission prompt — the one guardrail a non-technical user relies on.
- **`protect-tests.sh`**: JSON parsed with python3 (not grep/sed), and `.md`/`.txt` files are
  never blocked (notes under a `tests/` folder are not code tests).
- Repo weight: `.github/assets/social/` (~16 MB of unreferenced social-post graphics) removed
  from the tree — every clone was paying for images no doc references.

### Removed

- **BREAKING: `/memory-query`** (`query.py` + its command) — by the kit's own admission it
  rarely earned its subprocess; asking the agent in conversation covers it. `/memory-lint` and
  `/memory-usage` stay.
- `knowledge/log.md` — an orphaned append-only log nothing wrote to since `/memory-compile`
  was deleted in v4.2 (exactly the "quietly rotting chronicle" v5 exists to prevent).
- Dead constants in `config.py` left over from the retired v4 compile pipeline.

### Migration from v5.0

1. `git pull`. Your existing `.claude/memory/MEMORY.md` keeps working — it's simply untracked
   now (run `git rm --cached .claude/memory/MEMORY.md` in your own clone if git still tracks it).
2. If you enabled `/memory-query`, delete your copies (`.claude/commands/memory-query.md`,
   `.claude/memory/scripts/query.py`) — or keep them; they still run, just unsupported.
3. If you enabled the close-day layer, re-copy it (`cp -r .kit/advanced/close-day-layer/skills/close-day .claude/skills/close-day`) to drop the NSP writes.

## [5.0.0] — 2026-07-09 — Lean core: handoffs replace the daily chronicle; three memory caps; stale-refs detector

This release rebuilds the default around what actually survived long-running production use
(the maintainers run this pattern across their own repos). The chronicle-shaped defaults —
daily logs + the rolling next-session-prompt — were the parts that silently rotted: days went
unclosed, the NSP froze while still LOOKING authoritative (one production instance carried
phantom "open" items for 35 days), and MEMORY.md once packed 51.5 KB into 152 lines without
tripping the old line-count check. v5 keeps the kit's soul (date-tagged memory, audit-driven
promotion, "user only talks") and swaps the fragile layer for one that fails loudly.

### Changed

- **BREAKING: session close is `/close-session`, not `/close-day`.** The new ritual: capture
  dated patterns → audit for 3+-date repetition → promote on your "yes" → REPLACE the MEMORY.md
  header (current state, never a chronicle) → write a per-session handoff.
- **BREAKING: `context/next-session-prompt.md` retired.** "Where we left off" now lives in
  `context/handoffs/<topic>-<date>.md` — one immutable note per closed session; the SessionStart
  hook injects the newest one. No rolling file to rot.
- **BREAKING: `daily/` journal moved to opt-in `.kit/advanced/close-day-layer/`** together with
  the `/close-day` skill and the NSP template. One `cp` re-enables it (see that folder's README);
  it composes with the v5 core.
- **`session-start.py` rewritten:** injects newest handoff + memory stats + projects/experiments
  overview + knowledge index (budget trimmed 50K → 20K chars — the old injection was the single
  biggest per-session context tax).
- **`pre-compact.sh`** now requires MEMORY.md to be BOTH fresh and under its line cap before
  allowing compaction (fresh-but-oversized used to slip through).

### Added

- **Three independent MEMORY.md caps, hook-enforced: 180 lines / 32 KB / 3000 chars per line.**
  Line count alone lies — content densifies into ever-longer lines while `wc -l` stays flat.
  When any cap trips, the next session opens with an audit prompt.
- **Stale-refs detector** (`.claude/memory/scripts/stale-refs.py`): every session start, file
  paths mentioned in CLAUDE.md + MEMORY.md are checked against disk; unresolved ones are
  surfaced. The #1 memory failure is a stale belief that looks current — this catches the
  file-path class of it deterministically.
- **MEMORY.md header discipline:** the header is «current state», 2-3 sentences, replaced at
  every close. Chronicles belong in handoffs.
- **`context/handoffs/HANDOFF-TEMPLATE.md`** — the five-section session-close note.
- All docs synced to the lean core: README, CLAUDE.md, root SKILL.md, ARCHITECTURE, CONTRIBUTING,
  tour, knowledge/index, experiments/README, the starter BACKLOG, advanced/memory-usage — and the
  README diagrams (02-workflow, 03-layers, 04-promotion, 06-hooks) regenerated for v5.

### Migration from v4.2

1. Run `/close-day` one last time (if you used it), then copy your `daily/` folder anywhere you
   like — or enable the layer back: `.kit/advanced/close-day-layer/README.md`.
2. Turn your current `context/next-session-prompt.md` into the first handoff: save it as
   `context/handoffs/migrated-from-nsp-<today>.md`.
3. Replace `CLAUDE.md`, `.claude/hooks/`, `.claude/memory/MEMORY.md` header, and add
   `context/handoffs/` from v5. Your MEMORY entries, knowledge/, rules/, projects/ carry over as-is.
4. Or simplest, per the README: clone v5 fresh and tell Claude "I have a v4 kit at <path>, migrate it".

## [4.2.0] — 2026-06-03 — Default surface trimmed to two operators; usage telemetry + /close-day backfill

The three Python-backed memory commands were the heaviest, most developer-flavoured part of the kit — and where the v4.1.x defects lived. For the kit's non-technical audience the daily loop is fully covered by `/close-day` + `/tour`; the wiki-maintenance commands are power-user tooling. This release trims the default surface to those two, moves the rest to opt-in `.kit/advanced/`, and adds the two things the kit actually lacked: a data-driven "what's safe to prune" signal, and a way to recover days the user forgot to close.

### Removed

- **BREAKING: `/memory-compile`** — command + `compile.py` deleted. Auto-folding daily logs into wiki articles was unreliable in practice; `/close-day` already writes `knowledge/concepts/` articles directly, on the user's verbal "yes". This also removes the auto-write path that sat closest to the "user only talks" invariant.

### Changed

- **BREAKING: `/memory-lint` + `/memory-query` moved to `.kit/advanced/`.** They no longer auto-register as slash commands. `.kit/advanced/README.md` documents how to enable (copy into `.claude/`) and why each was demoted. The default operator set is now just `/close-day` + `/tour`.
- **`lint.py` dropped the orphan-sources check** (it depended on the removed compile state file): 6 checks → 5.
- **All docs synced** to the new split — README, CLAUDE.md, root SKILL.md, ARCHITECTURE.md, tour, CONTRIBUTING, daily/README, knowledge/index.

### Added

- **`/memory-usage`** (`aggregate_usage.py` + `usage_config.py`) in `.kit/advanced/` — a read-only telemetry report parsed from your Claude Code session transcripts: **hot files** (used a lot, recently) vs **cold candidates** (zero reads in 30 days → safe to archive). Turns "what can I prune?" into data instead of a guess, and feeds the `/close-day` archival proposal. Stdlib-only, writes one report, never touches memory — invariant-safe. (Ported from the maintainers' production stack.)
- **`/close-day` auto-backfill of missed working days.** New Phase 0 (gap analysis): before synthesizing today, the skill finds working days (non-merge commits) in the last 14 days with no `daily/YYYY-MM-DD.md`, shows them, takes one batch approval, and reconstructs each from git history (commit messages + `[YYYY-MM-DD]` MEMORY tags). Backfilled days are marked as reconstructed and never invented; pauses for confirmation if >7 days are missing; skips silently when there's no git. Removes the "remember to run it every day" burden — one call catches up the layer.
- **MEMORY.md overflow nudge** in `session-start.py` — when MEMORY.md exceeds 200 lines, the injected context now carries a one-line prompt to run `/close-day` (promote settled patterns, prune absorbed ones). Display-only; no automatic writes.

### Migration from v4.1.x

1. **If you used `/memory-compile`** — stop; it's gone. `/close-day` writes concept articles directly now.
2. **If you used `/memory-lint` or `/memory-query`** — copy them back from `.kit/advanced/` (see that folder's README): `cp .kit/advanced/scripts/*.py .claude/memory/scripts/ && cp .kit/advanced/commands/*.md .claude/commands/`.
3. **To try `/memory-usage`** — same copy step, then run `/memory-usage` after you have a few weeks of sessions.
4. No changes needed to your memory content — only the command surface moved.

---

## [4.1.3] — 2026-06-03 — Audit cleanup: repair /memory-query, drop dead code & doc drift

A full audit of the v4.1.2 tree surfaced three real defects and several doc-drift items left over from the v4.1.0 minimization. No architecture change — this release makes the shipped code match what the docs already claim.

### Fixed

- **BREAKING (for anyone scripting against it): `/memory-query` was dead on arrival.** `query.py` imported `CONNECTIONS_DIR`, a constant removed from `config.py` in v4.1.0 when `knowledge/connections/` + `knowledge/meetings/` were collapsed into `concepts/`. The command raised `ImportError` before doing anything. The v4.1.0 cleanup updated `compile.py` and `lint.py` but missed `query.py`. Dropped the stale import and its prompt reference; verified the module imports and `lint.py` / `compile.py --dry-run` stay green.

### Removed

- **4 committed macOS Finder duplicate files** — `compile 2.py`, `config 2.py`, `lint 2.py`, `query 2.py` under `.claude/memory/scripts/`. They were the pre-v4.1.0 versions (still referencing the removed `CONNECTIONS_DIR` / `MEETINGS_WIKI_DIR` layers) — junk and actively misleading.
- **`flush.py`** — the CHANGELOG marked it removed back in v4.0.0-alpha.1 ("auto-flush was unreliable and invariant-violating — spawned behind the user's back"), but the 235-line file was still shipping. Not wired by any hook, and it directly contradicts the load-bearing "user only talks, agent writes" invariant. Deleted.

### Changed

- **Root `SKILL.md` rewritten to the real v4.1 architecture.** It still advertised the dead v4.0.0 shape: version `4.0.0`, "role-based reference skills (`user-invocable: false`)", a `/memory-audit` operator, and "four layers". Now: two core invariants, three memory layers (`daily/` → `MEMORY.md` → `knowledge/concepts/`) plus `.claude/rules/`, the 5 shipped commands, `projects/` + `experiments/`. Version `4.1.3`.
- **`protect-tests.sh`** comment scrubbed — it leaked private project names ("poker tests, lead-gen tests") into the public template. Replaced with a generic description of the conventions it matches.
- **`context/next-session-prompt.md`** active-project name aligned from `_example_client` to the shipped `projects/my-first-project/`.

### Note

The v4.0.0 "16-test verification suite" was evidently not re-run after the v4.1.0 layer removal — it checks that "Python scripts compile + import", which would have caught the `query.py` regression. Re-running it (or a CI equivalent) before each release is recommended.

---

## [4.1.2] — 2026-04-27 — Tighten CLAUDE.md operational instructions

Patch — close 3 operational gaps in the auto-loaded agent brain so Claude Code doesn't need to read `.kit/` docs or guess for common operations. CLAUDE.md grew by zero lines (replaced existing items with tighter versions).

### Changed

- **Experiment creation:** `experiments/<name>-YYYYMMDD/EXPERIMENT.md` autonomous-write now mandates copying `experiments/EXPERIMENT-TEMPLATE.md` as starting structure (no invented schemas)
- **Rule creation:** `.claude/rules/*.md` write-with-confirmation now explicitly requires `created:` + `last-reviewed:` frontmatter (pointer to `_example.md.disabled` skeleton)
- **Concept creation:** `knowledge/concepts/*.md` write-with-confirmation now explicitly references `knowledge/index.md` for frontmatter spec
- **Experiment closing:** distill ritual essentials inlined in CLAUDE.md (lessons → concepts/, code → projects/, then `rm -rf` folder) so the agent doesn't need to read close-day SKILL body just to close an experiment

### Why

User feedback: "the user is not going to read files — Claude Code must understand everything from auto-loaded context." Audit showed `.kit/ARCHITECTURE.md`, `experiments/README.md`, `EXPERIMENT-TEMPLATE.md`, and skill bodies don't auto-load. The 3 most common operations (create experiment, create rule, close experiment) had operational details only in non-auto-loaded files. v4.1.2 inlines the essentials in CLAUDE.md.

---

## [4.1.1] — 2026-04-27 — Restore experiments/ + canonicalize date-tagging

Two corrections to v4.1.0 minimization:

1. **`experiments/` was wrongly removed.** v4.1.0 deleted the layer as "undocumented opt-in pattern", but it's a real working pattern (24+ active experiments in production use). Restored with proper documentation as the sandbox layer next to `projects/`.
2. **Date-tagging was implicit, not explicit.** The mechanism worked (`/close-day` reads date-tagged MEMORY entries) but was nowhere stated as a load-bearing convention. New users couldn't see WHY the date format matters. Promoted to a documented system invariant alongside "user only talks".

### Added

- **`experiments/`** layer fully restored as documented sandbox.
  - `experiments/README.md` — convention, lifecycle, agent triggers
  - `experiments/EXPERIMENT-TEMPLATE.md` — hypothesis / method / result / lessons skeleton
  - Naming: `<descriptive-name>-YYYYMMDD` (date-tagged, aligned with kit-wide convention)
  - Lifecycle: open → work → distill on close (lessons → `knowledge/concepts/`, code → `projects/`, then delete folder; git history retains)
  - `/close-day` flags experiments older than 30 days for closure
- **Date-tagging convention as load-bearing system invariant.**
  - New section in `.kit/ARCHITECTURE.md` — "Date-tagging convention (load-bearing)" — explains where dates live and why they matter
  - `CLAUDE.md` rewritten — two core invariants: "user only talks" + "every memory entry carries a date tag"
  - `.claude/rules/_example.md.disabled` — frontmatter now includes `created` + `last-reviewed` date fields, plus a "Review history" section
  - `knowledge/index.md` — frontmatter spec adds `created:` field; section-append convention `## [YYYY-MM-DD] section title` for in-article evolution tracking
  - `context/next-session-prompt.md` — every Pick-up / Open-decisions / Recent-deliverables item must be `[YYYY-MM-DD]`-prefixed; Active experiments section added
  - `daily/TEMPLATE.md` — clarifies date-is-in-filename, optional `[HH:MM]` for in-day cross-reference, audit candidates cite triggering dates
  - `.claude/memory/MEMORY.md` — adds "Why dates matter" section; entries without date tag declared a bug
  - `.claude/skills/close-day/SKILL.md` — Phase 2 audit explicit date-arithmetic queries; Signal E (experiment hygiene) added; example proposals quote specific dates as evidence

### Changed

- **CLAUDE.md projects-vs-experiments table** added; `experiments/` in Architecture-at-a-glance map; agent triggers documented ("let's experiment with..." → creates experiment, not project)
- **`.kit/ARCHITECTURE.md` `experiments/<name>-YYYYMMDD/` layer** described next to `projects/<name>/` with explicit "different lifecycle, different quality bar, no direct promotion" semantics
- **README.md** "What's inside" tree adds `experiments/` line; one-paragraph projects-vs-experiments summary added below tree

### Migration from v4.1.0

If you adopted v4.1.0:

1. Existing rules — add `created` + `last-reviewed` to frontmatter (use `git log --reverse --pretty=format:%aI -- .claude/rules/<name>.md | head -1` to find created date)
2. Existing concepts — add `created` field to frontmatter
3. NSP entries — date-prefix existing items (use git blame or just timestamp them today as "carry-over from earlier")
4. If you want experiments — create `experiments/` folder, copy `EXPERIMENT-TEMPLATE.md` from this release

No code changes required — the date-tagging machinery in `lint.py`/`compile.py` already worked; this release makes the convention explicit so new contributors and future-you understand why.

---

## [4.1.0] — 2026-04-27 — Kit minimization

After two weeks of dogfooding v4.0.0 on real production work, several layers turned out to be noise that the kit shouldn't ship by default. v4.1.0 trims them out. The pattern can still be added per-project by users who want it (see `.kit/ARCHITECTURE.md` "Adding role-guidance yourself"); the kit just doesn't seed templates anymore.

### Removed

- **BREAKING: 7 role-guidance reference-skill seeds.** `design-guidance`, `dev-guidance`, `editorial-guidance`, `marketing-guidance`, `seo-geo-guidance`, `product-guidance`, `founder-profile` deleted from `.claude/skills/`. Generic role wisdom seeds were noise — what works for content marketing is wrong for SaaS dev is wrong for editorial. Pattern documented in ARCHITECTURE for opt-in.
- **BREAKING: `/memory-audit` operator.** Was paired with role-guidance for oversized-skill split detection. With seeds gone, the operator lost its purpose. Removed: `.claude/commands/memory-audit.md`, `.claude/skills/memory-audit/`, `lint.py --audit-sizes` flag, `check_oversized_reference_skills` function, `OVERSIZED_SKILL_LINES` + `REFERENCE_SKILL_SUFFIX` + `SKILLS_DIR` constants.
- **BREAKING: `knowledge/connections/` and `knowledge/meetings/` subdirs.** Nobody filled them; `compile.py` only ever wrote to `concepts/`. Collapsed `knowledge/` to a single subdir. `CONNECTIONS_DIR` + `MEETINGS_WIKI_DIR` removed from `config.py`. `compile.py` prompt no longer instructs the sub-Claude to create connections/ articles. `lint.py` only scans `concepts/`.

### Changed

- **Kit-meta moved to `.kit/`.** `CHANGELOG.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `VERSION` no longer pollute the project root after clone. Users get a clean root for their own project's docs. README at root links into `.kit/` for kit history.
- **Promotion pipeline simplified from 4 phases to 3.** Liquid (daily) → Amber (MEMORY) → Crystal (rules OR concepts). The role-skill intermediate phase is gone.
- **`/close-day` audit Phase 2 retargeted.** Was: surface candidates for promotion to `<role>-guidance/SKILL.md`. Now: surface candidates for `knowledge/concepts/<topic>.md` articles or `.claude/rules/<name>.md` constraints.
- **`/memory-lint`** now runs 6 checks (was 7). Dropped: oversized reference skills.
- **README rewritten in English.** Was Russian (v4.0.0); v4.1.0 reverts to English for git compatibility with international contributors.
- **All Russian dialogue examples in skills, CLAUDE.md, ARCHITECTURE.md replaced with English equivalents.** Agent's actual conversation with the user can be in any language; the documentation examples are in English.

### Added

- **`daily/TEMPLATE.md`** — explicit format for what `/close-day` produces. Tracked in git (was not present before).
- **`.kit/` subfolder** to host kit-meta separated from user project root.

### Migration from v4.0.0

If you adopted v4.0.0 and want v4.1.0:

1. **If you wrote content into role-guidance files** — move it. Open each `.claude/skills/<role>-guidance/SKILL.md` you populated and either: (a) translate stable judgment patterns to `.claude/rules/<topic>.md`, or (b) translate the rationale-rich entries to `knowledge/concepts/<topic>.md`. Then delete the `<role>-guidance/` directory.
2. **If you used `/memory-audit`** — stop. The operator is gone. If a task skill genuinely grows past 500 lines, split it manually or wait until enough projects need this and we re-add the operator with a wider target.
3. **If you wrote into `knowledge/connections/` or `knowledge/meetings/`** — move content to `knowledge/concepts/` (single subdir from now on). Update any `[[connections/X]]` or `[[meetings/Y]]` wikilinks to `[[concepts/X]]`/`[[concepts/Y]]`.
4. **If your tooling expected CHANGELOG.md / ARCHITECTURE.md / VERSION at root** — they're under `.kit/` now. Update paths.

### Why

700+ session dogfooding showed: kit users either (a) ignored the role-guidance seeds entirely (most), or (b) deleted them and built their own (some). The seeds added cognitive load on first install and never paid off. Same for `connections/` + `meetings/` — sounded useful in theory, never filled in practice. Kit ships only what every user needs; everything else is opt-in pattern.

---

## [4.0.0] — 2026-04-26 — Promoted from alpha; replaces v3.2.2 in main repo

After two weeks of dogfooding the v4.0.0-alpha branch on real production work, v4 is promoted to stable. v3.2.2 stays accessible via the `v3.2.2` git tag for anyone who still needs it; the `main` branch now reflects v4 architecture.

### Verified working

Sixteen-test verification suite passed cleanly on the migrated repo (settings.json valid + all hook paths exist; bash hooks pass syntax check; Python scripts compile + import; skills aggregator symlinks resolve; runtime tests on every hook with synthetic stdin; `lint.py` + `compile.py --dry-run` clean; cross-references resolve for all six slash commands; `config.py` paths exist for all 8 layer constants). Discovered + patched in process: `lint.py` and `compile.py` were treating `daily/README.md` as a daily log; both now skip `README` / `TEMPLATE` / `INDEX` stems.

### Added

- **`.claude/settings.json`** registering all 5 hooks (SessionStart / PreCompact / Stop / SessionEnd / PreToolUse-Edit|Write). With `$CLAUDE_PROJECT_DIR`-anchored paths and per-hook timeouts (15-30s). Without this file the hook scripts on disk were inert.
- **`daily/.gitkeep` + `.claude/state/.gitkeep`** so the directories survive `git clone`. `.gitignore` updated to allow `daily/README.md` through.

### Changed

- **VERSION** `4.0.0-alpha.2` → `4.0.0`.
- **Reference skills now ship populated.** v4-alpha shipped 7 empty role templates (design / dev / editorial / marketing / seo-geo / product / founder-profile). v4.0.0 adds `memory-audit` task skill alongside the existing `close-day` + `tour`, bringing the included slash-command set to six (`/close-day`, `/memory-audit`, `/memory-compile`, `/memory-lint`, `/memory-query`, `/tour`).
- **`marketing-guidance` description** — removed legacy «playbooks» token; replaced with «patterns» throughout.
- **`daily/README.md`** — pointer to `.claude/skills/<role>-guidance/SKILL.md` instead of the deleted `playbooks/*.md`.
- **`.gitignore`** — replaced legacy «Memory Kit v2» comment header.
- **`.claude/rules/_example.md` → `_example.md.disabled`** — Claude Code only auto-loads `.md` rules; the `.disabled` suffix prevents the scaffold-template rule from loading as if it were a real rule.

### Fixed

- **`lint.py:check_orphan_sources`** — was reporting `daily/README.md` as «uncompiled daily log». Now skips `README` / `TEMPLATE` / `INDEX` stems.
- **`compile.py:list_daily_logs`** — same fix.
- **`config.py`** — removed dangling `ARCHIVE_DIR` constant pointing at a non-existent `archive/` directory.

### Resolved (from v4.0.0-alpha.1 known issues)

- **Skill aggregator symlinks** — now wired up. `skills/close-day`, `skills/memory-audit`, `skills/tour` each symlink into `.claude/skills/<name>/SKILL.md` so Claude Code aggregators that scan repo roots find them.
- **GitHub remote** — v4 lives on `awrshift/claude-memory-kit` `main` from this release. v3.2.2 is preserved at the `v3.2.2` tag.

### Migration from v3.2.x

If you have a v3.2 project and want to use v4:

1. **Don't merge v4 into your v3 project.** The folder layout differs enough that an in-place merge produces inconsistent state.
2. Clone v4 fresh as a sibling project: `git clone https://github.com/awrshift/claude-memory-kit.git my-project-v4`.
3. In the new project's first session, say "we're migrating from v3.2, here's my old project: ~/Desktop/my-old-kit".
4. Agent walks the old project, proposes which content lives in which v4 layer, you approve verbally, agent writes patches.

Specifically the agent will handle:
- `experiences/*.md` — review each entry; promote to `.claude/skills/<role>-guidance/SKILL.md` or discard as one-off
- Old `MEMORY.md` — re-tag with dates, fold into v4 `MEMORY.md`
- `knowledge/concepts/*.md` — copy verbatim (same layer in v4)
- `daily/*.md` — copy verbatim
- `.claude/rules/*.md` — copy verbatim
- `playbooks/*.md` (if you had them in your v3 project) — translate to `.claude/skills/<role>-guidance/SKILL.md` with proper frontmatter

---

## [4.0.0-alpha.2] — 2026-04-24 pm — Anthropic-alignment refactor

After researching Anthropic's official Claude Code primitives (`code.claude.com/docs/en/skills`, `code.claude.com/docs/en/memory`, `code.claude.com/docs/en/best-practices`), we realised the v4.0.0-alpha draft had invented a custom `playbooks/` layer that maps 1:1 to Anthropic's **reference content skills** (skills with `user-invocable: false`). Reclassification in this release:

### Changed

- **BREAKING: `playbooks/*.md` → `.claude/skills/<role>-guidance/SKILL.md`.** Seven role files moved and rewritten with YAML frontmatter: `name`, `description` (keyword-rich for auto-invocation), `user-invocable: false`. Claude auto-loads them whenever the conversation matches the description — no custom trigger table.
- **CLAUDE.md simplified.** Removed the four-layer layer map section's `playbooks/` line; removed the anti-pattern «don't edit playbooks». Added explicit «don't maintain custom trigger keyword tables» rule — Claude's native description-matching replaces that.
- **ARCHITECTURE.md** — layer map, promotion pipeline, and «What's NOT in the architecture» updated. Promotion pipeline phase 3 now reads: `daily → MEMORY → reference skill (via /close-day) → rule (via stability + 6+ months)`.
- **README.md** — terminology swapped throughout; directory tree updated to show reference skills under `.claude/skills/`.
- **SKILL.md (root)** — mentions «role-based reference skills» instead of «role-based playbooks». Version bumped to 4.0.0-alpha.2.
- **`/close-day` skill (`SKILL.md`)** — audit proposals now target `.claude/skills/<role>-guidance/SKILL.md`.
- **`/memory-audit` skill (`SKILL.md`)** — scans `.claude/skills/*-guidance/SKILL.md` for the 500-line threshold. Split proposals create new reference-skill directories, not new playbook files.
- **`scripts/lint.py` + `scripts/config.py`** — `check_oversized_playbooks` renamed to `check_oversized_reference_skills`. `PLAYBOOKS_DIR` constant removed; `SKILLS_DIR` added with glob filter `*-guidance/SKILL.md`.
- **`/memory-lint` + `/memory-audit` slash commands** — docs updated to match.

### Removed

- **BREAKING: `playbooks/` directory.** All 7 seed files (design, dev, editorial, marketing, seo-geo, product, founder-profile) + `README.md` deleted. Content preserved in the new reference skills under `.claude/skills/<role>-guidance/SKILL.md`.

### Why this alignment matters

- Anthropic actively maintains the skills primitive. Using it means we inherit future improvements (subagent preloading, path-scoping via `paths:`, managed-settings deployment, plugin packaging) for free.
- Auto-invoke via `description` matching replaces a custom trigger table we would have had to hand-maintain in every project's CLAUDE.md.
- Progressive disclosure is automatic: description is always in context, body loads only when auto-triggered. No more custom «loading on trigger» logic.
- Reference skills compose with task skills (`/close-day`, `/memory-audit`) through the same file format — one thing to learn.

### Migration (within v4 scaffold, for anyone who cloned 4.0.0-alpha.1)

```bash
# If you have the old scaffold locally with content in playbooks/:
# 1. Move each playbooks/<role>.md → .claude/skills/<role>-guidance/SKILL.md
# 2. Rewrite frontmatter: add `name`, `description` (keyword-rich), `user-invocable: false`
# 3. Body stays the same; remove role:/status:/load-triggers: from old frontmatter
# 4. Delete playbooks/ folder
# 5. Reload Claude Code to pick up the new skills
```

For users coming from v3.2 directly, ignore this and read the 4.0.0-alpha.1 migration section below — the v3.2 → v4 cut already doesn't have `playbooks/`.

---

## [4.0.0-alpha.1] — 2026-04-24 am — Agent-audit-ritual architecture

> **BREAKING.** v4 is not backward-compatible with v3.2. Do not merge in-place. Start a fresh project; if you want to bring v3.2 content over, tell the agent "we're migrating from v3.2" and it will walk you through manual import.

### Why this release exists

v3.2 introduced `experiences/` as a staging layer for patterns, and a background `promote-patterns.py` script to auto-detect 3× repetitions. After real use we killed both:

1. **Cross-session automatic detection is unreliable.** Without a persistent background process, matching semantics across session boundaries via signature heuristics misses more than it finds.
2. **The scaffold stayed empty.** After deploying `experiences/` no entries accumulated; no case of «I wish I'd caught X earlier» arose.
3. **Automation threatens the core invariant.** «User only talks, agent writes» breaks the moment a background script surfaces patterns the user feels obliged to review and edit.

v4 replaces automation with a daily ritual. `/close-day` is an audit-in-session where the agent reads today's daily log + MEMORY.md, compares against existing playbooks, and surfaces promotion candidates verbally. User says "yes"; agent writes the patch. Higher quality, lower infrastructure cost, invariant preserved.

### Added

- **`playbooks/`** — role-based tacit wisdom. One file per role: `dev.md`, `design.md`, `editorial.md`, `marketing.md`, `seo-geo.md`, `product.md`, `founder-profile.md`. Loaded on trigger-match. Different axis from `knowledge/concepts/` (facts + rationale) — no overlap.
- **`/memory-audit`** operator + skill — two-phase structural check for oversized playbooks (free grep-size flag → agent-in-session semantic clustering → split execution on user "yes").
- **`--audit-sizes`** flag on `/memory-lint` — fast pre-step that runs only the oversized-playbook check.
- **Oversized-playbook detection** in `lint.py` — flags any `playbooks/*.md` over 500 lines as split candidate.
- **`projects/<name>/`** structure for multi-project isolation. Shared layers (CLAUDE.md, MEMORY.md, rules, playbooks, concepts) load always; per-project BACKLOG + materials load when user says "we're working on <name>".
- **`projects/_example_client/BACKLOG.md`** — template for new projects.
- **Extended `/close-day` SKILL.md** — explicit audit ritual: synthesize → read MEMORY + playbooks → surface 0-4 candidates → write on verbal approval.
- **`PLAYBOOKS_DIR` + `OVERSIZED_PLAYBOOK_LINES`** constants in `config.py`.
- **Root `SKILL.md`** — aggregator-registry metadata for v4.
- **`CHANGELOG.md`** — this file.

### Changed

- **`/close-day`** is now the single promotion mechanism. Previously ambiguous whether promotion happened automatically (via `promote-patterns.py`) or manually (user-edited files). Now: always audit ritual, always agent-written, always on user "yes".
- **`/memory-lint`** now runs 7 checks (was: 6). New: `check_oversized_playbooks()`.
- **`session-end.sh` hook** simplified — no auto-flush, just SessionEnd timestamp logging. End-of-day synthesis is user-invoked via `/close-day`.
- **`CLAUDE.md`** and **`ARCHITECTURE.md`** rewritten around the «user only talks» invariant.
- **`README.md`** rewritten to lead with the agent-audit value prop, not the file-layout explanation.

### Removed

- **BREAKING: `experiences/`** layer — `README.md`, `TEMPLATE.md`, all staged entries. Over-engineered for a problem that didn't materialize.
- **BREAKING: `scripts/flush.py`** — replaced by `/close-day` user-invoked ritual. Auto-flush via `flush.py` was unreliable (transcripts not always present, `claude -p` subprocess flakiness) and invariant-violating (spawned behind the user's back).
- **`promote-patterns.py`** — scrapped before implementation; the entire class of auto-detection scripts is out of scope for v4.
- **Optional auto-flush block in `session-end.sh`** — commented-out code removed entirely. If anyone wants background synthesis, it belongs in a separate tool, not the core kit.

### Deprecated

(none — v4 is a clean cut, not a gradual migration)

### Security / safety

- **"User only talks" invariant is load-bearing.** Any future contribution that proposes a background script writing to memory files without user "yes" will be rejected.
- All existing safety hooks (`pre-compact.sh`, `periodic-save.sh`, `protect-tests.sh`) preserved. They capture state before loss events; they do not promote patterns.

### Migration from v3.2.2

Do NOT try to merge v4 into a v3.2 repo. The folder layout is different enough that a merge produces inconsistent state.

Recommended path:

1. Clone v4 as a fresh project
2. In the new project's first session, say: "we're migrating from v3.2, here's my old project: ~/Desktop/my-old-kit"
3. Agent scans the old project, proposes which content to import and where it fits in the new 4-layer model
4. You approve each import verbally; agent writes patches into the v4 layout
5. Old project stays untouched as backup until you're confident v4 is working

Agent will specifically handle:
- `experiences/*.md` entries → propose promotion to `playbooks/<role>.md` or discard as one-off
- Old `MEMORY.md` entries → re-tag with dates, fold into v4 `MEMORY.md`
- Old `knowledge/concepts/*.md` → copy verbatim (same layer in v4)
- Old `daily/*.md` → copy verbatim
- Old `.claude/rules/*.md` → copy verbatim

### Known issues

- **`/memory-audit` semantic clustering has no regression test.** Agent judgment on "2-4 independent clusters" can be wrong on the edge. Always preview the proposal before saying "yes"; you can say "show details" and the agent will show which entries land in which split file.
- **No GitHub remote yet.** v4 lives locally on the author's desktop; first public release will push to a fresh repo (not overwrite v3.2).
- **Skill aggregator symlinks** — `skills/` root with symlinks into `.claude/skills/` (the v3.2.1 pattern) is not yet wired up. Decision deferred to post-alpha testing.

---

## [3.2.2] — 2026-04-XX (last v3.x)

Final pre-v4 version. See the v3.2 repo for changes prior to this shift.

---

## Version numbering

- **Major (v4.x)** — breaking architecture changes (layer additions/removals, invariant shifts)
- **Minor (v4.N.x)** — new skills, new commands, new rule templates
- **Patch (v4.N.P)** — bug fixes, doc improvements, no user-visible API change

v4.0.0-alpha = first scaffold; v4.0.0 ships when all 11 scaffold TODOs are closed and the kit has been used for a full week without contradiction.
