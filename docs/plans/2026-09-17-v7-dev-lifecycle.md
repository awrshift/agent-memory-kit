# v7 dev-lifecycle — spec

**Created:** 2026-09-17 · **Status:** decided
**Authority:** ssot for this slice · **Design:** `docs/V7-DESIGN.md`

> This file is the CONTRACT an `executor` builds to. Decided by the main session BEFORE any
> agent is spawned. An executor never edits this file — a forced deviation is REGISTERED in its
> report and adjudicated by the integrator at merge.

## Goal

Add the development-lifecycle layer to the plugin in `plugins/memory-kit/`: workflow tiers,
AC-IDs and value sources in specs, the input-coverage gate in `executor`, the `assumed` spec
status, session-start surfacing of owed decisions, two new skills (`document`, `code-sync`),
AC binding in `qa-sweep` and `review-loop`, a hot-path budget in the repo checker, and the
docs that must stay true in the same change.

## Non-goals

- No new memory layer, no new top-level directory in the user's repo beyond `projects/<name>/`.
- No `scope` skill, no `verify` skill, no `scout`/`researcher` agents, no Haiku anywhere.
- No change to `hooks/pre-compact.sh`, `hooks/protect-tests.py`, `hooks/session-end.sh`.
- No change to the four memory layers' formats, caps or promotion rules.
- No rewrite of existing skill bodies beyond the lines the slices name. No "while I'm here" edits.
- No change to `.opencode/` or `docs/specs/*` (host specs) in this round.
- Do not touch `~/dev/claude-memory-kit` (the `main` worktree). All work is in this worktree.

## Acceptance — pre-registered

| # | What will prove this worked | How it is checked |
|---|---|---|
| AC-1 | `SPEC-TEMPLATE.md` Acceptance rows use `AC-n` ids and have a `Verified` column; a `## Value sources` section exists; the status line lists `assumed` | read the file |
| AC-2 | `README-TEMPLATE.md` (project) carries a `**Workflow tier:**` line with the four values and one-line meanings; `BACKLOG-TEMPLATE.md` task block has an optional `**Tier:**` override | read the files |
| AC-3 | `agents/executor.md` runs the input-coverage test before building, stops on an owed decision with a fixed report shape, and on an explicit "build anyway" writes `plans/<date>-<slug>-assumed.md` from a shipped template | read the file; the template exists at `templates/workspace/project/ASSUMED-SPEC-TEMPLATE.md` |
| AC-4 | `templates/rules/orchestration.md` gains ONE line naming the gate; the file stays ≤ 30 lines | `wc -l` |
| AC-5 | `hooks/session-start.py` stats show, per project, the count of `assumed` specs and of `building` specs older than 14 days; nothing shown when zero; virgin repo still writes nothing | the CI probe in `checks.yml` extended with a fixture that has one assumed spec and one old building spec; `grep` on the hook output |
| AC-6 | `skills/document/SKILL.md` exists with modes `pr` · `changelog` · `release-note` · `postmortem`; each draft is built from `git diff`/`git log` output the skill runs itself; four templates in `skills/document/templates/`; the description line triggers on "write the PR", "changelog", "postmortem", "release note" | read; `tools/check-repo.py` passes (frontmatter present) |
| AC-7 | `skills/code-sync/SKILL.md` exists: walks `projects/*/plans/*.md` with status `building`/`assumed`, checks code evidence, flips `building → done` only with a named gate, marks `stale` with the reason, lists `assumed` specs owed ratification, updates the project README `Last verified`; surgical edits only, never rewrites prose | read; a dry-run section in the skill states what it never does |
| AC-8 | `skills/qa-sweep/SKILL.md` and `agents/qa.md`: run scope names the spec and its `AC-n`; each finding row carries an `AC` column (or `—`); the run record has a per-AC pass/fail table; the integrator fills the spec's `Verified` cells | read the diff; no other lines changed |
| AC-9 | `reference/review-loop.md`: registry row gains an `AC` column; `reference/orchestrator-fact-check.md` unchanged | read |
| AC-10 | `tools/check-repo.py`: new check 7, hot-path budget: every `skills/*/SKILL.md` ≤ 24 000 bytes and every `agents/*.md` ≤ 8 000 bytes, warning printed at 90 %, failure over 100 %; current tree passes | run `python3 tools/check-repo.py` → exit 0 |
| AC-11 | `VERSION`, `plugins/memory-kit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, `plugins/memory-kit/.cursor-plugin/plugin.json` all read `7.0.0-dev` | `python3 tools/check-repo.py` |
| AC-12 | `context/identity.md` names the two new operators and the tier in ≤ 6 added lines; `docs/ARCHITECTURE.md` gains a "v7: the development lifecycle" section; `docs/CHANGELOG.md` has a `[7.0.0-dev]` entry; root `README.md` builders' block and `plugins/memory-kit/README.md` skill table list `document` and `code-sync` | read; `check-repo.py` link check passes |
| AC-13 | `claude plugin validate ./plugins/memory-kit` passes | run it |
| AC-14 | Full CI equivalent passes locally: `check-repo.py`, the five SessionStart profiles with the CANARY, the virgin-repo guard, PreCompact, test guard | run the commands from `.github/workflows/checks.yml` |

## Value sources

| Value | Source |
|---|---|
| Tier names and meanings | `docs/V7-DESIGN.md` table row "Rigor dial" |
| Spec status set | `draft · decided · building · done · superseded · assumed · stale` (this spec) |
| "old building" threshold | 14 days (this spec; constant in the hook, env-overridable `CMK_SPEC_STALE_DAYS`) |
| Hot-path byte ceilings | 24 000 / 8 000 (this spec; measured: today's largest SKILL.md is `test`-class ~16 KB in comparable kits) |
| Assumed spec filename | `plans/YYYY-MM-DD-<slug>-assumed.md` (this spec) |

## Gates

```bash
cd ~/dev/claude-memory-kit-v7
python3 tools/check-repo.py
claude plugin validate ./plugins/memory-kit
# SessionStart profiles + virgin guard + PreCompact + test guard: the exact shell from
# .github/workflows/checks.yml, run locally with CLAUDE_PLUGIN_ROOT=$PWD/plugins/memory-kit
```

## Slices

| # | Slice | Files it owns | Depends on |
|---|---|---|---|
| S1 | Templates + executor gate + orchestration line (AC-1..4) | `plugins/memory-kit/templates/workspace/project/{SPEC-TEMPLATE,BACKLOG-TEMPLATE,README-TEMPLATE}.md`, new `ASSUMED-SPEC-TEMPLATE.md`, `plugins/memory-kit/agents/executor.md`, `plugins/memory-kit/templates/rules/orchestration.md` | — |
| S2 | Session-start surfacing + CI probe (AC-5) | `plugins/memory-kit/hooks/session-start.py`, `.github/workflows/checks.yml` | — (reads the status line format from S1's spec: `**Status:** assumed` / `building`, `**Created:** YYYY-MM-DD`) |
| S3 | `document` skill (AC-6) | new `plugins/memory-kit/skills/document/**` | — |
| S4 | `code-sync` skill (AC-7) + one pointer line in `skills/close-session/SKILL.md` "Also check" | new `plugins/memory-kit/skills/code-sync/**`, `plugins/memory-kit/skills/close-session/SKILL.md` (one line) | — |
| S5 | AC binding in QA + review (AC-8, AC-9) | `plugins/memory-kit/skills/qa-sweep/SKILL.md`, `plugins/memory-kit/agents/qa.md`, `plugins/memory-kit/reference/review-loop.md`, `plugins/memory-kit/reference/qa-PROTOCOL-TEMPLATE.md` | — |
| S6 | Checker budget + version + docs (AC-10..12) | `tools/check-repo.py`, `VERSION`, all manifests, `plugins/memory-kit/context/identity.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, `README.md`, `plugins/memory-kit/README.md` | S1–S5 merged (it documents them) |

S1–S5 touch disjoint files and run in parallel. S6 runs after.

## Inputs the executor is given

- `CLAUDE.md` at the repo root (paths, "never write into a repo that didn't ask", validate commands).
- `docs/V7-DESIGN.md` (the design; binding on intent).
- The existing file(s) the slice owns, read in full before editing.
- House style for kit docs: English, terse, instruct don't justify; a skill's `description` is
  written for a router; bodies load on invoke, so depth is allowed there but not in rules.
- Model rule: any `model:` in an agent file is `opus` or `sonnet`, never `haiku`.

## Open questions

None blocking. Deferred to evaluation: whether `code-sync` should also touch `.claude/rules/`
(v7 answer: no, rules are promoted only via `close-session` on a yes).

## Registered deviations (filled at merge, by the integrator)

| # | What the executor hit | Why | Accepted / rejected |
|---|---|---|---|
