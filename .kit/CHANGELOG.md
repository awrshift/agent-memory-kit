# Changelog

All notable changes to Memory Kit are documented here. Breaking changes marked **BREAKING**.

## [4.2.0] — 2026-06-03 — Default surface trimmed to two operators; usage telemetry + /close-day backfill

The three Python-backed memory commands were the heaviest, most developer-flavoured part of the kit — and where the v4.1.x defects lived. For the kit's non-technical audience the daily loop is fully covered by `/close-day` + `/tour`; the wiki-maintenance commands are power-user tooling. This release trims the default surface to those two, moves the rest to opt-in `.kit/advanced/`, and adds the two things the kit actually lacked: a data-driven "what's safe to prune" signal, and a way to recover days the user forgot to close.

### Removed

- **BREAKING: `/memory-compile`** — command + `compile.py` deleted. Auto-folding daily logs into wiki articles was unreliable in practice; `/close-day` already writes `knowledge/concepts/` articles directly, on the user's verbal "yes". This also removes the auto-write path that sat closest to the "user only talks" invariant.

### Changed

- **BREAKING: `/memory-lint` + `/memory-query` moved to `.kit/advanced/`.** They no longer auto-register as slash commands. `.kit/advanced/README.md` documents how to enable (copy into `.claude/`) and why each was demoted. The default operator set is now just `/close-day` + `/tour`.
- **`lint.py` dropped the orphan-sources check** (it depended on the removed compile state file): 6 checks → 5.
- **All docs synced** to the new split — README, CLAUDE.md, root SKILL.md, ARCHITECTURE.md, tour, CONTRIBUTING, daily/README, knowledge/index.

### Added

- **`/memory-usage`** (`aggregate_usage.py` + `usage_config.py`) in `.kit/advanced/` — a read-only telemetry report parsed from your Claude Code session transcripts: **hot files** (used a lot, recently) vs **cold candidates** (zero reads in 30 days → safe to archive). Turns "what can I prune?" into data instead of a guess, and feeds the `/close-day` archival proposal. Stdlib-only, writes one report, never touches memory — invariant-safe. (Ported from the maintainers' production rnd-hub stack.)
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
