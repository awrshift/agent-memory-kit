# Orchestration invariants

> Install this file into `.claude/rules/` only if you delegate work to subagents. It is
> ALWAYS loaded, so every line here costs context in every future session — keep it this short.
> Depth lives in the plugin's `reference/` docs, read on demand.

1. **A subagent or reviewer report is INPUT, never a fact.** Re-run the gate, read the
   file:line, query the store yourself before saying "done" — and read at least one real output
   end to end yourself; a helper may pre-sort, it never replaces the reading.
2. **Subagents execute a decided spec** — a FILE at `projects/<name>/plans/`, named in the
   prompt, carrying Goal · Non-goals · pre-registered Acceptance · Gate commands · slices, and the
   Depth pass · Practice · Review lines (`SPEC-TEMPLATE.md`, `reference/spec-depth.md`). They never
   redesign; a forced deviation is REGISTERED in the report and adjudicated at merge.
3. **An executor builds nothing until every value its slice produces has a named source in the
   spec** — a gap is an OWED DECISION reported back, never invented. An override is written to
   disk as an `assumed` spec, never left in chat.
4. **The main session is the single integrator** — it alone writes memory and everything under
   `projects/<name>/`, merges worktrees, and re-runs the full gate set on the merged tree.
   Subagent-green is not integrated-green.
5. **A failing test means the CODE is wrong**, not the test.
6. **Never count reviewer votes — adjudicate on merits.** One dissenter with a file:line beats
   three abstract agreements; a repo-reading reviewer outranks a brief-only one on code facts.
7. **Resume a subagent only for a short follow-up on the same work.** Its context only grows —
   a resumed agent carries its whole history into every step (one executor reached 288k tokens on
   an 8-branch review round). A new task, another branch set, or any follow-up once its report
   shows ≳ 150k tokens → a FRESH agent with a brief that points at files. Slice big jobs so one
   run stays well under that.
8. **Every count in a report comes from a saved script or command cited next to it**; a hand
   tally is a draft until the script agrees. A cause told to the user states how many of all the
   rows it holds for, and the rows that do not fit.
9. **The user decides what only the user can:** scope (what they get), external actions
   (a push, a PR, a message others see), irreversible data operations, and spend beyond the limit
   they set. Technical choices inside that scope are the agent's — reported as «decision · why it
   is correct · what would prove it wrong», not asked as questions.

Deeper procedure: `orchestrator-fact-check` (acceptance layers + claim→check table),
`spec-depth` (depth pass, practice, review stake, fail branches, outcome over proxy),
`parallel-development` (fan-out defaults, stop-conditions), `review-loop` (triage, diff gate,
findings registry), `doc-governance` (one SSOT per fact), `decisions-log` (the lean ledger) — all
in the plugin's `reference/` directory.
