# Memory Kit v7 — the development lifecycle layer

> Design, 2026-09-17. Branch `v7/dev-lifecycle`, worktree `~/dev/claude-memory-kit-v7`.
> The build spec executors work from is `docs/plans/2026-09-17-v7-dev-lifecycle.md`.
> Origin: the JSM "Agentic Engineering" workflow (nine skills, `jsmastery-pro/skills`)
> compared against v6.5.4 in `~/dev/SE System Design/foundation/06-workflow-comparison.md`.

## The one-paragraph version

v6 solves two layers well: **memory between sessions** (hot cache, handoffs, knowledge, rules,
all dated, capped, promoted on a yes) and **orchestration** (the main session decides, an
`executor` builds to a spec file, reports are INPUT, never facts). What it does not cover is the
middle: the **development lifecycle** itself, from a task to a decided spec, to a build that
refuses to invent decisions, to proof against the spec, to a human-readable record, to a
reconciliation of documents with code. v7 adds exactly that, **without a fifth memory layer**.
Everything new lives in `projects/<name>/` (the work's own documents) and in operators that
walk it. One thread runs through all of it: **numbered acceptance criteria**.

## What v7 keeps untouched

- The four memory layers, their caps, the date rule, promotion on a yes. `identity.md`'s line
  stands: a new memory layer is how this system dies.
- `executor` / `recon` / `idea-validator` / `qa` as the agent set; the model split
  (Fable/Opus orchestrates, Opus builds, Sonnet reads; never Haiku).
- `orchestrator-fact-check`, `review-loop` with its findings-class registry and the
  promotion-on-third-occurrence rule, `parallel-development`, `doc-governance`.
- "Suggestions, never gates" is **not** adopted. Two gates stay hard: a failing test means the
  code is wrong; a spec with unresolved open questions is not `decided`.

## What v7 adds, layer by layer

| Lifecycle step | v6.5.4 | v7 |
|---|---|---|
| Rigor dial | implicit | **Workflow tier** per project (`prototype` · `alpha` · `beta` · `ga`), one default in `projects/<name>/README.md`, overridable per task in `BACKLOG.md`. Read by `executor` (which tail to recommend), `qa-sweep`, `review-loop` |
| Task | `BACKLOG.md` with `T-NNN` | unchanged, plus an optional `Tier:` override and a required `Spec:` pointer or "none, too small" |
| Decision | `plans/YYYY-MM-DD-<slug>.md` (Goal · Non-goals · Acceptance · Gates · Slices) | Acceptance rows carry stable IDs `AC-1…n`. New section **Value sources**: every value the slice must produce, compute or display, with its named source. New status `assumed` (recorded by an executor's override, never by the integrator's design) |
| Build gate | executor registers deviations **after** building | executor runs the **input-coverage test before the first file**: enumerate values → check each has a source in the spec → any gap is an OWED DECISION → stop and report. Override path: the integrator may say "build anyway"; the executor then writes `plans/YYYY-MM-DD-<slug>-assumed.md` (status `assumed`, the assumption, who authorised, code area) and builds against it |
| Proof | `qa-sweep` lenses, integrator reproduces | unchanged mechanics; every finding and every run record names the `AC-n` it exercises; the spec's Acceptance table gains a `Verified` column (date + how) filled by the integrator |
| Review | second-opinion, session-review, findings registry | unchanged; the registry row gains an `AC` column where applicable |
| Human record | none | new skill **`document`**: PR body · changelog entry · release note · postmortem, written **from `git diff` / `git log`**, never from the model's memory of what it did. Templates shipped |
| Reconcile code ↔ documents | `close-session` reconciles the session with memory | new skill **`code-sync`**: after a merge, walk specs in `building`, confirm code matches, mark `done` / flag `stale`; surface `assumed` specs owed ratification; update project README map and `Last verified`. Surgical edits only |
| Session entry | stats: caps, projects touched, handoff | stats gain one line per project: `N specs assumed (owed ratification) · M building > 14 d` — hook-side, zero LLM |
| Kit hygiene | `tools/check-repo.py` (manifests, hooks, links) | plus a **hot-path budget**: each `SKILL.md` and agent body under a byte ceiling, a warning at 90 %, so the kit cannot bloat the way it audits others for |

## The acceptance-criteria thread

```
spec Acceptance AC-3 ──▶ executor slice S2 "serves AC-3" ──▶ test names AC-3
        │                                                       │
        ▼                                                       ▼
qa run record "AC-3: pass, 2026-09-20, walked path X"   review-findings row · AC-3
        │
        ▼
spec Acceptance table: Verified = 2026-09-20 · qa-run-20260920.md
```

A `done` that cannot be traced to a `Verified` cell is `IN PROGRESS`. This is the existing
"a DONE nobody verified is IN PROGRESS" rule, now with an address.

## Ownership (one writer per file, extended)

| File | Created by | Changed by |
|---|---|---|
| `projects/<name>/README.md` (map, tier default) | setup / integrator | integrator; `code-sync` updates `Last verified` and map rows |
| `BACKLOG.md` | integrator | integrator; `code-sync` may flip a status line it can prove |
| `plans/*.md` (specs) | integrator, before any fan-out | integrator (content, status); `executor` only creates an `*-assumed.md` and never edits a spec; `code-sync` flips `building → done/stale` status lines only |
| `qa/qa-run-*.md` | `qa-sweep` | nobody |
| `review-findings.md` | integrator | integrator |
| `CHANGELOG.md`, PR body, `docs/releases/`, `docs/postmortems/` | `document` | `document`, humans |
| `.claude/memory/MEMORY.md`, handoffs, knowledge, rules | unchanged (v6) | unchanged |

## Not in v7 (deliberately)

- **No `scope` skill.** `BACKLOG.md` + tier + spec pointer already answer "what, in what
  order, how heavy". A second planning artifact would drift from the first.
- **No thin `CLAUDE.md → AGENTS.md` pointer by default.** Stays a `setup` offer (T2 hosts).
- **No `verify` skill separate from `qa-sweep`.** The lenses stay; the AC binding is the change.
- **No Haiku agents.** `scout`/`researcher` are not adopted; `recon` on Sonnet covers both.
- **No "suggestions only".** See gates above.

## Versioning

`7.0.0-dev` on this branch. `VERSION`, `plugin.json`, both marketplaces carry the same string
(the repo checker enforces it). The install path for a lab test:
`claude --plugin-dir ~/dev/claude-memory-kit-v7/plugins/memory-kit` in a lab repository,
never in a repository that runs the v6 plugin from the marketplace.

## Evaluation plan (before merging to main)

Same task through v6 (marketplace install) and v7 (lab install), artifacts compared, not
impressions. Recorded in `~/dev/SE System Design/backlog.md` (Decision log):

1. A feature with a hidden decision (a value whose source is not in the spec). Did the v7
   executor stop? What did v6 register?
2. One `qa-sweep` on the same running product. Do v7 findings carry `AC-n`? Is the spec's
   `Verified` column filled at the end?
3. `document pr` on the same diff vs a hand-written PR body. Anything invented?
4. `code-sync` after a merge with one spec that the code silently diverged from. Flagged?
5. Session start stats in a lab repo with two `assumed` specs. Shown?

## [2026-09-19] Evaluation testbed and the planned seventh slice

**Testbed.** The five steps above are run in a real project, not the toy lab: `~/dev/factcheck-agent`
(a Python/LangGraph claim-verification service, spec `docs/spec.md` there). Launch:
`claude --plugin-dir ~/dev/claude-memory-kit-v7/plugins/memory-kit` with the marketplace v6 disabled in
that repo's `.claude/settings.json`. What that repo already carries in v7 form: `AC-1…7` with a `Verified`
column, `## Value sources` (17 rows; the values that had no prior source were ratified as its D-011),
`**Workflow tier:** prototype`, slices with a `Serves` column. Mapping of the plan: step 1 = its executor on
slice S0/S1 (does the gate stop on any value that slipped the table?); step 2 = its first `qa-sweep` with
`AC-n`; step 3 = `document pr` on its S1 diff; step 4 = `code-sync` after S1 merge; step 5 = its session
start once an `assumed` spec exists. Evidence for each step is filed in that repo
(`context/handoffs/`, `projects/.../qa/`) and summarised here before merge. `~/dev/memory-kit-v7-lab` is superseded.

**Planned slice S7 — evidence** (from `docs/research/openresearch-comparison-2026-09-19.md`, alphaXiv/OpenResearch, MIT;
no fifth layer, no infrastructure):
1. `EXPERIMENT-TEMPLATE.md`: fields `branch`, `run command`, `result run id`, `frozen: yes/no`; rule: a run that
   produced any result freezes the experiment, a new hypothesis is a new experiment, never an edit.
2. `reference/orchestrator-fact-check.md`: "validate before reporting" checklist (the log names the variant and
   config; the final metric is present; the trajectory is recoverable; truncated output is not evidence of absence).
3. `templates/rules/orchestration.md` (two lines max): claims about code cite `file:lines`; measured results cite
   the run/gate output that was read, never a status.
4. `reference/parallel-development.md`: before starting, inspect branches other sessions have claimed
   (`git branch -a`, worktree list); one branch, one owner.
5. `templates/rules/orchestration.md` (same two lines): a wait/notification is a signal, not the source of truth;
   re-read state on every wake.
Not adopted: OpenResearch's SQLite experiment store (a database) and its autonomous-loop default.
