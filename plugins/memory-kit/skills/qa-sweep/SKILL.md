---
name: qa-sweep
description: >
  Run a multi-lens agent QA sweep of the RUNNING product: spawn `qa` agents (one per lens —
  user-flow · edge-state · honesty · contract · ux-critique), collect their structured
  findings, integrator-verify the load-bearing ones, and land verified findings as backlog
  tickets + a run record in docs/qa/. Use whenever the user asks to QA, test, or probe the
  product from the user's side — "qa sweep", "test the UI", "walk the flows", "find
  inconsistencies", "check how this looks to a client" — and proactively after integrating any
  large UI slice, before a milestone, or when a manual walk found one bug and siblings are
  likely. Trigger even when the user names only one angle (e.g. "check the API errors") — pick
  the matching lens subset. NOT for unit testing (your test suite does that) and NOT a
  replacement for the integrator's own acceptance walk.
---

# QA Sweep — multi-lens agent QA of the live product

Read `docs/qa/README.md` FIRST (the protocol SSOT: environment rules · the five lens briefs ·
findings format · triage) — the lens briefs in agent prompts come verbatim from there, and the
account/mutation policy it sets is a hard rail, not advice. If that file doesn't exist yet,
create it from the layer's protocol template (`${CLAUDE_PLUGIN_ROOT}/reference/qa-PROTOCOL-TEMPLATE.md` in
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
3. **Spawn `qa` agents** with the lens brief from the protocol § Lens briefs + the run scope
   (which screens/flows changed recently — QA the delta first, then one broad pass).
4. **Verify before ticketing (the fact-check rule):** reproduce every P1/P2 finding yourself
   (the named repro steps) before it becomes a ticket. Unreproducible → back to the agent or
   drop with a note. «Impressions» never become tickets directly.
5. **Land the results:** verified findings → backlog tickets (P1/P2) or a minors batch (P3) ·
   one run record `docs/qa/qa-run-YYYYMMDD.md` (lenses run · coverage · findings table with
   verified/dropped status · pointers to tickets) · a row in the protocol's § Runs index.
6. **Cleanup:** stop dev servers, remove stray screenshots from the repo root, re-seed the
   sacrificial account if a mutation run dirtied it.
