# OpenResearch (alphaXiv) vs agent-memory-kit — comparison, 2026-09-19

Method: Sonnet recon, read-only; kit v6.5.4 + v7 dev branch (local), OpenResearch via GitHub API/WebFetch (5,325 stars, 325 forks, MIT, created 2026-06-07, pushed 2026-09-19, Rust CLI + local UI on 127.0.0.1:4791, SQLite store, 12 skills, 13+ contributors). Filed by the integrator; numbers are a one-day snapshot.

## Surprises
1. OpenResearch's evidence gate ("never infer a result from run status or memory", frozen nodes, mandatory `<run id>` / `<file path lines>` tags in chat) and the kit's `reference/orchestrator-fact-check.md` ("a report is INPUT, never a source of record") are the same invariant reached independently: convergent design, not a gap.
2. The kit's unshipped v7 (`AC-n` acceptance ids, `Value sources` table, executor input-coverage gate, `assumed` spec status) is the same idea applied to specs.
3. OpenResearch's worktree protocol is more explicit: one branch = one worktree owner, "check `git branch -a` before starting" (orx-git). The kit states worktree isolation as a rule without the "inspect other sessions' claimed branches" step.
4. "Telemetry" means opposite things: OpenResearch = vendor usage analytics (opt-out, install id); kit = local self-audit of whether its own layers ever fired (`system-audit` lens 4, `usage.py`). Do not conflate.

## OpenResearch mechanisms
- Experiment tree: project = tree of nodes, each node an `orx/<slug>` git branch inheriting parent code AND run command verbatim ("vary code, not knobs-in-the-command"); the runner builds an immutable source archive from the recorded commit (uncommitted files never run).
- Frozen-node invariant: a run that produces ANY result freezes the branch ("a disappointing result is still a result"); an erroring run leaves the node provisional (repair in place, cap 2 non-answering runs → ask the user). A bad result cannot be erased, only escaped by a visible child branch.
- Tree doctrine: "stacked bushes" (fan siblings within a round, descend onto the winner) vs anti-patterns "flat fan" and "noodle".
- Loop: propose one round's co-equal hypotheses → branch → implement → `orx exp run` → `orx exp wait` ("a sleep-until-change signal, not the source of truth"; re-read `orx runs` on every wake) → repair / refill / promote / stop; stop after goal or ~3 consecutive failed/regressed runs.
- Evidence: results live only in run logs (`orx logs`); "if a run's result is not in its log, it cannot be inspected later"; validate before reporting (log names variant + config, final metric present, trajectory recoverable, byte window really contains the output, "truncated output is not evidence of absence").
- Hypothesis/result record: one free-form markdown field per node (`orx exp desc`), overwrite not append; no schema.
- Delegation: `orx agent spawn` = helper session with its own worktree and transcript, cannot nest, capped concurrency. Literature retrieval loop is never delegated: the main agent ranks candidates itself (`orx discover keyword|embedding|openalex|biorxiv`, `orx paper`).
- Skills (12): experiment-tree, create, compute (hf/modal/k8s/ssh/slurm/ray/local), git, evidence, agent-delegation, lit-review, paper (LaTeX), reports, figures, customize, instances. Distribution: `orx install-skills` into Claude Code, Codex, OpenCode, Cursor, Antigravity.
- Human decision points: autonomous by default; asks on repair-cap breach and backend choice.
- Evals of the tool itself: none public (CI = fmt/clippy/test).

## Domain matrix

| Domain | OpenResearch | Kit | Direction |
|---|---|---|---|
| Memory and continuity | none (per-node notes only) | MEMORY.md + handoffs + SessionStart profiles | kit > OR |
| Experiment / evidence tied to commits | branch per node, frozen nodes, immutable archive, log as evidence | `experiments/<name>-YYYYMMDD/EXPERIMENT.md`, free text, no branch field, no freeze | OR > kit |
| Verifying agent claims | validate-before-reporting + frozen nodes + evidence tags (structural) | orchestrator-fact-check, system-audit step 3, qa evidence rules (procedural) | equal, different enforcement |
| Parallel isolation | worktree per node, `agent spawn`, "check `git branch -a` first" | parallel-development.md, executor `isolation: worktree`, one integrator | OR > kit on collision protocol |
| Literature / research | built-in academic search, anti-delegation rule | dated filing convention `projects/<name>/research/` | OR > kit |
| Human decision points | autonomous by default, narrow asks | approval-as-default everywhere | kit > OR |
| Telemetry | vendor analytics | local self-audit of layer usage | different purposes |
| Distribution across harnesses | 5 harnesses via skill install | 5 harnesses with evidence-labelled specs, CI probes for 2 | equal breadth; kit better evidenced |
| Evals of the kit/tool | none | hook-behaviour CI (5 probes) + v7 lab (manual) | kit > OR |

## Reusability
- Both MIT (2026). Skills are structurally the same shape (frontmatter + markdown) but OR's assume the `orx` CLI/store substrate: patterns transfer, files do not.
- Compatible with the "no fifth layer / no infrastructure" invariant: (a) frozen-node + branch fields as an addition to EXPERIMENT-TEMPLATE.md (`branch:`, `run command:`, `frozen: yes/no`, `result run id:`); (b) the validate-before-reporting checklist as prose in orchestrator-fact-check.md; (c) inline evidence tags as a prompt convention (no filesystem footprint); (d) the "inspect other sessions' branches before starting" step in parallel-development.md; (e) "wait signals are not the source of truth, re-read state on every wake" as a line in orchestration rules.
- Incompatible: the SQLite experiment store (a database = the category the kit's README rejects); the autonomous-loop default (contradicts approval-as-default).

## Unknowns
`orx.db` schema; backend specifics; contributor count beyond 13; the kit's idea-validator.md not re-read; OR's Antigravity support is absent from the kit's spec table.
