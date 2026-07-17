# Orchestration layer (opt-in since v5.1)

Multi-agent working mode for people who use the kit to BUILD things (software, agent systems,
research pipelines) rather than only to remember. Distilled from the maintainers' production
practice across hundreds of real sessions. The core memory kit works fine without it — enable
this when you start delegating work to subagents.

## The model split (why this layer exists)

One session, three roles:

- **The integrator (your main session)** — designs, decides, merges, and ALONE writes shared
  state (MEMORY.md, backlogs, docs). Everything a subagent reports is INPUT, never a fact.
- **Executors** — build to an already-decided spec in an isolated git worktree. They never
  redesign; forced deviations are REGISTERED in their report and adjudicated at merge.
- **Recon agents** — read-only fact-gatherers. Raw facts with file:line pointers; never a
  design, never a recommendation.

Parallelism is the desired mode: fan out independent recon / build chunks / reviews, keep the
integrator as the single merge point. Subagent-green ≠ integrated-green — the integrator re-runs
the gates on the merged tree.

## Enable

```bash
# from the kit root
mkdir -p .claude/agents
cp .kit/advanced/orchestration-layer/agents/*.md .claude/agents/
cp .kit/advanced/orchestration-layer/rules/*.md  .claude/rules/
cp -r .kit/advanced/orchestration-layer/skills/* .claude/skills/
```

Then append this block to your `CLAUDE.md` (the agent reads it every session):

```markdown
## Orchestration invariants
1. A subagent/reviewer report is INPUT — re-run the gate, read the file:line, query the
   store YOURSELF before claiming "done" (see rules/orchestrator-fact-check.md).
2. Subagents execute a decided spec; deviations are REGISTERED, never silently applied.
3. The main session is the single integrator: alone writes shared docs, merges worktrees,
   re-runs the full gate set on the integrated tree.
4. A failing test means the CODE is wrong, not the test.
5. Never count reviewer votes — adjudicate on merits; one dissenter with a file:line beats
   three abstract agreements.
```

## Contents

- `agents/executor.md` — the builder agent (worktree isolation by default, registered deviations)
- `agents/recon.md` — the read-only fact-gatherer
- `agents/idea-validator.md` — isolated adversarial critic (no parent context, strict verdict format)
- `skills/session-review/` — `/session-review`: the end-of-session adversarial review loop
  (brief → parallel reviewers → adjudicate → apply/plan/challenge → retro on the machine)
- `skills/second-opinion/` — `/second-opinion`: cross-check a high-stakes answer before
  committing (Devil's Advocate · Boardroom Debate · Round-Table); pairs the isolated
  idea-validator with an external-family model when you have one
- `rules/orchestrator-fact-check.md` — "a report is input": the three acceptance layers +
  the claim-class → cheapest-decisive-check table
- `rules/parallel-development.md` — fan-out defaults, worktree isolation, stop-conditions
- `rules/doc-governance.md` — anti-drift: one SSOT per fact, grep-sweep on change, label-don't-bury
- `rules/decisions-log.md` — a lean append-only ledger of numbered decisions (`D-001`, `D-002`…)

Each rule is generic — no project-specific gates baked in. Where a rule says "your gates",
substitute your project's own (typecheck, lint, tests, build).
