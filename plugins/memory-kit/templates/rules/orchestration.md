# Orchestration invariants

> Install this file into `.claude/rules/` only if you delegate work to subagents. It is
> ALWAYS loaded, so every line here costs context in every future session — keep it this short.
> Depth lives in the plugin's `reference/` docs, read on demand.

1. **A subagent or reviewer report is INPUT, never a fact.** Re-run the gate, read the
   file:line, query the store yourself before saying "done".
2. **Subagents execute a decided spec.** They never redesign; a forced deviation is REGISTERED
   in the report and adjudicated at merge.
3. **The main session is the single integrator** — it alone writes shared state (memory,
   backlogs, docs), merges worktrees, and re-runs the full gate set on the merged tree.
   Subagent-green is not integrated-green.
4. **A failing test means the CODE is wrong**, not the test.
5. **Never count reviewer votes — adjudicate on merits.** One dissenter with a file:line beats
   three abstract agreements; a repo-reading reviewer outranks a brief-only one on code facts.

Deeper procedure: `orchestrator-fact-check` (acceptance layers + claim→check table),
`parallel-development` (fan-out defaults, stop-conditions), `review-loop` (diff gate + findings
registry), `doc-governance` (one SSOT per fact), `decisions-log` (the lean ledger) — all in the
plugin's `reference/` directory.
