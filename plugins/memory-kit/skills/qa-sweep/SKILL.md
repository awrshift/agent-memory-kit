---
name: qa-sweep
description: >
  Run a multi-lens agent QA sweep of the RUNNING product: spawn `qa` agents (one per lens —
  user-flow · edge-state · honesty · contract · ux-critique), collect their structured
  findings, integrator-verify the load-bearing ones, and land verified findings as backlog
  tickets + a run record in the project's qa/ folder. Use whenever the user asks to QA, test, or probe the
  product from the user's side — "qa sweep", "test the UI", "walk the flows", "find
  inconsistencies", "check how this looks to a client" — and proactively after integrating any
  large UI slice, before a milestone, or when a manual walk found one bug and siblings are
  likely. Trigger even when the user names only one angle (e.g. "check the API errors") — pick
  the matching lens subset. NOT for unit testing (your test suite does that) and NOT a
  replacement for the integrator's own acceptance walk.
---

# QA Sweep — multi-lens agent QA of the live product

Read `projects/<name>/qa/README.md` FIRST (the protocol SSOT: environment rules · the five lens briefs ·
findings format · triage) — the lens briefs in agent prompts come verbatim from there, and the
account/mutation policy it sets is a hard rail, not advice. A project that predates this layout
may keep its protocol elsewhere — wherever its `CLAUDE.md` points, or at `docs/qa/README.md`,
`context/qa/PROTOCOL.md`, `.claude/rules/qa-sweep.md`, or in a project-local `qa-sweep` skill.
Look there before scaffolding: an existing protocol is the SSOT
wherever it lives, its run records go next to it, and a second protocol must never be created
beside it. Only when no protocol exists anywhere,
create one from the layer's protocol template (`${CLAUDE_PLUGIN_ROOT}/reference/qa-PROTOCOL-TEMPLATE.md` in
the kit repo — copy it from there if this project only adopted the layer's `.claude/` files)
and fill the placeholders before sweeping.

## Steps
1. **Preflight (integrator, by hand):** bring up the stack the protocol names (app · API ·
   store) · pick the account per the protocol's policy (the demo/real account = OBSERVE-ONLY
   always; the seeded sacrificial account = mutation QA only when the run brief grants it) ·
   make sure nothing else is writing to the shared store during the sweep (no integration test
   suites, no live jobs).
2. **Pick lenses** for this run (default: user-flow + contract in parallel, then edge-state,
   then honesty + ux-critique). Browser lenses run CONCURRENTLY via the isolated Playwright MCP
   servers the protocol lists (one server per concurrent browser agent — mechanism + logged-in
   seed recipe in the protocol § Parallel lenses). Browser lenses: user-flow · edge-state ·
   ux-critique. Non-browser: contract (curl) · honesty (curl + read-only store queries).
3. **Spawn `qa` agents** with the lens brief from the protocol § Lens briefs + the run scope.
   The run scope MUST name: the governing spec (`projects/<name>/plans/YYYY-MM-DD-<slug>.md`),
   the `AC-n` ids under test from that spec's Acceptance table, the project's workflow tier
   (from `projects/<name>/README.md`, or the task's `Tier:` override in `BACKLOG.md`), and which
   screens/flows changed recently — QA the delta first, then one broad pass. At tier
   `prototype` no sweep is expected: say so and stop.
4. **Verify before ticketing (the fact-check rule):** reproduce every P1/P2 finding yourself
   (the named repro steps) before it becomes a ticket. Unreproducible → back to the agent or
   drop with a note. «Impressions» never become tickets directly. A «pass» on an AC counts only
   when you reproduced the walked path yourself or ran the check named in that AC's «How it is
   checked» cell — an agent's report alone never passes an AC.
5. **Land the results:** verified findings → backlog tickets (P1/P2) or a minors batch (P3) ·
   one run record `projects/<name>/qa/qa-run-YYYYMMDD.md` (lenses run · coverage · a per-AC table
   `AC | result (pass/fail/not exercised) | evidence` · findings table with an `AC` column
   (`—` when the finding ties to no AC) and verified/dropped status · pointers to tickets) · a
   row in the protocol's § Runs index. After landing, fill the spec's `Verified` cell for every
   AC that passed — the date + `qa/qa-run-YYYYMMDD.md`.
6. **Cleanup:** stop dev servers, remove stray screenshots from the repo root, re-seed the
   sacrificial account if a mutation run dirtied it.

## Rails that hold even when the protocol is silent
- **Cross-channel evidence:** an action's evidence comes from a different channel than the action
  — after a click, read the network response, the DOM or the store, never «the click looked fine».
- **A clean bill is a claim:** it names the oracle it ran and the commit it ran against. A clean
  bill without an oracle is recorded as «not reached», never as clean.
- **No real credentials in a QA agent's hands** — seeded storage state or a sacrificial login only;
  a report can leak whatever the agent was given.
- **Coverage is a queue:** seed the next brief from the previous run's «not reached» list and name
  the data archetype; a third consecutive run on the same archetype changes archetype.
- **Solve once, write it down:** a verified finding becomes a permanent regression test; a golden
  path that two consecutive runs walk clean is codified as an e2e spec and dropped from later
  briefs unless its surface changed — the lens explores, the spec remembers.
