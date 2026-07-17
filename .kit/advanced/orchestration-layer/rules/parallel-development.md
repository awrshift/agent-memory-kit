---
created: 2026-07-17
last-reviewed: 2026-07-17
---

# Parallel development — desired, not merely tolerated

Parallelism is the wanted mode wherever feasible without architecture cost.

## Level 1 — intra-session fan-out (the default; use aggressively)

- Fan out independent work: recon sweeps ‖ external fresh-checks ‖ build chunks ‖ adversarial
  review — launched in the SAME message so they run concurrently.
- **Worktree isolation** whenever parallel chunks MUTATE files; the main agent merges.
- **The main agent is the single integrator:** alone writes shared docs (MEMORY.md, backlogs,
  handoffs, the decision ledger), merges worktrees, and re-runs the FULL gate set on the
  INTEGRATED tree — subagent-green ≠ integrated-green.
- **Subagents are executors only:** they build to a decided spec or gather facts; design
  belongs to the integrator. A forced deviation is REGISTERED in the report and adjudicated
  at merge — never silently applied.

## Level 2 — multi-session tracks (two genuinely independent tracks)

Only with ALL of: (1) disjoint modules/files/migrations · (2) an own branch/worktree per
session · (3) decoupled test state (separate DBs, or serialize the runs) · (4) decisions
written to per-session shard files, folded into shared docs by the LAST finisher.

## Stop-conditions (go sequential instead)

Overlapping files or schema · a pending one-way-door decision that steers both tracks · a task
smaller than the coordination cost · never split one slice's acceptance criteria across
sessions.

**Invariants that never bend for speed:** the per-change definition of done · pre-registered
acceptance ("what will prove this worked", written BEFORE building) · one SSOT per fact /
a single writer for shared docs · the simplicity default.
