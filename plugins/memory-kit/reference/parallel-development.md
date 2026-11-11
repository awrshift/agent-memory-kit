---
created: 2026-07-17
last-reviewed: 2026-11-11
---

# Parallel development — desired, not merely tolerated

Parallelism is the wanted mode wherever feasible without architecture cost.

## Level 0 — the spec exists as a FILE before anyone fans out

Fan-out multiplies whatever the spec says, including what it forgot to say. So the contract is
written first, by the main session, at `projects/<name>/plans/YYYY-MM-DD-<slug>.md`
(`templates/workspace/project/SPEC-TEMPLATE.md`), and each executor prompt POINTS at that path
instead of restating it. A spec pasted into N prompts is N specs that drift the moment one is
amended; a spec that lives only in a prompt cannot be re-read at merge, cannot be diffed against
what was built, and is gone by the next session. Its Acceptance section is pre-registered — written
BEFORE building, or it is not acceptance — its rows carry stable `AC-n` ids that slices, tests and
QA runs quote, its `## Value sources` table names where every value comes from, and its status may
be `assumed` (an executor's recorded override, owed ratification) or `stale`. The spec is
integrator-owned: executors read it, never edit it.

## Level 1 — intra-session fan-out (the default; use aggressively)

- Fan out independent work: recon sweeps ‖ external fresh-checks ‖ build chunks ‖ adversarial
  review — launched in the SAME message so they run concurrently.
- **Worktree isolation** whenever parallel chunks MUTATE files; the main agent merges.
- **The main agent is the single integrator:** alone writes shared and project docs (MEMORY.md,
  handoffs, everything under `projects/<name>/` — backlog, plans, ledger, findings registry),
  merges worktrees, and re-runs the FULL gate set on the INTEGRATED tree — subagent-green ≠
  integrated-green.
- **Subagents are executors only:** they build to a decided spec or gather facts; design
  belongs to the integrator. A forced deviation is REGISTERED in the report and adjudicated
  at merge — never silently applied.
- **Every helper call names a role and an explicit model;** the roster, the role templates and what a helper that
  starts without the project's rules must be told: `helper-roster.md`.

## Level 2 — multi-session tracks (two genuinely independent tracks)

Only with ALL of: (1) disjoint modules/files/migrations · (2) an own branch/worktree per
session · (3) decoupled test state (separate DBs, or serialize the runs) · (4) decisions
written to per-session shard files, folded into shared docs by the LAST finisher.

**One integrating session and several windows** is the other shape: one main session owns decisions, merges and shared
docs, the others build one task each from a brief file and report. Its cycle, close order, brief lines, size limits and
resource slots: `window-cycle.md`.

## Held work drifts

**Applies when:** finished work waits unsent — for a review, a merge, a release — while the branch it targets moves.

- **Re-base held lines at the session's start.** Fetch the target, dry-run a merge of each top of the held work; a top
  with a conflict, or one that should be built on another top and is not, makes the first task of the session: re-base
  each line's root and the heads stacked on it, re-run the gates on the result; the next build starts from the
  re-based top (in trial in one project since 2026-11-10; count due at its next six acceptances).
  Why: every held line of one project conflicted with its target within 0.4–1.2 days, with 5–10 textual conflicts each;
  the conflicts sat at each line's shared base, so one re-base of the root clears every block stacked on it. Re-basing
  only at acceptance leaves the next acceptance on the same line a day behind again
  (measured in one project, 2026-11: every held top conflicted within 1.2 days).
- **An acceptance names every other held top it does not contain** — under a heading «Other tops», one line each:
  hash and one word (parallel · to merge · merged · dropped · sent). A small script at the acceptance commit can refuse
  one that does not; compare by commit subject when re-bases rewrite hashes (in trial in one project since 2026-11-10;
  count due at its next six acceptances).
  Why: two accepted slices in one project rode on no line — every later build and test run went without them — and
  a helper's table had claimed one of them contained; only a containment run found it
  (measured in one project, 2026-11: 2 accepted slices on no line).

## Stop-conditions (go sequential instead)

Overlapping files or schema · a pending one-way-door decision that steers both tracks · a task
smaller than the coordination cost · never split one slice's acceptance criteria across
sessions.

**Flow limits.** An item whose actual time passes twice its estimate goes to the user as «continue / reshape / stop»,
with the evidence — not silently continued. Work waiting for someone else's review gets a cap (open requests at one
reviewer), so the waiting work is taken sooner instead of piling up (one project's working practice; no count).

**Invariants that never bend for speed:** the per-change definition of done · pre-registered
acceptance ("what will prove this worked", written BEFORE building) · one SSOT per fact /
a single writer for shared docs · the simplicity default.
