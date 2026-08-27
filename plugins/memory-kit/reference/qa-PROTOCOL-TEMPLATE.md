# Agent QA Harness — protocol (TEMPLATE)

> Copy this file to `projects/<name>/qa/README.md` and fill every `<placeholder>`. One
> protocol per project — the environment, accounts and journeys it names are that product's,
> and a shared protocol across projects sends a lens at the wrong app.
> This file is the protocol SSOT: the `/qa-sweep` skill executes it; the `qa` agent type
> (the plugin's `agents/qa.md`) is the worker. Run records live beside it in the same folder.

Standing multi-lens QA of the RUNNING product by `qa` agents (Playwright + curl + read-only
store queries), findings verified by the integrator before they become tickets. Complements —
never replaces — (a) your test suites, (b) any design-time review you run, and (c) the
integrator's own acceptance walk.

## Environment  *(fill in)*
- Stack: `<how to start the app>` (`<app URL>`) · `<how to start the API>` (`<API URL>`) ·
  background workers only when job flows are in scope. Dependencies: `<db/cache/etc + ports>`.
- **Account policy — TWO accounts, two modes:**
  - **Demo / real account** (`<login>`): **OBSERVE-ONLY, always** — state-changing buttons,
    create/delete actions, and anything that spends quota or money are FORBIDDEN: they would
    pollute real data. Login is the one allowed mutation.
  - **Sacrificial QA account** (`<login>` / seeded by `<reseed command>`): **mutation QA
    allowed** when the run brief explicitly grants it — approve/reject flows, decide races,
    double-click idempotency. Re-seed before a run for a known-state fixture; re-seed after a
    destructive run to restore it. Make the seed deterministic (same command → same fixture)
    so findings are reproducible.
- **Parallel browser lenses:** each concurrent browser lens gets its OWN isolated Playwright
  MCP server — the project `.mcp.json` defines `playwright-qa` + `playwright-qa-b` (see this
  layer's `mcp.json.example`), both `@playwright/mcp --isolated` (in-memory profile → zero
  cross-lens collision) with `--caps=testing,devtools` (the `browser_verify_*` machine oracles
  + tracing/video) and `--test-id-attribute=<your testid attribute>`. Assign one server per
  browser lens; N concurrent browser lenses = N isolated servers (add more `playwright-qa-*`
  entries the same way). Non-browser lenses parallelize freely. Integration test suites must
  NOT run during a sweep if they share the store.
- **Seed a logged-in lens (optional):** generate a storage-state once and point the server at
  it: `npx playwright open --save-storage=.claude/qa/seed-storage-state.json <login URL>`
  (log in as the run's account, close the window), then append
  `--storage-state=.claude/qa/seed-storage-state.json` to that server's args. The seed holds a
  session cookie → gitignore `.claude/qa/`, never commit it, regenerate when it expires.
- Store cross-checks: `<read-only query command + access notes>`. Beware access-control traps:
  a restricted role that sees 0 rows is NOT an empty database — document the right role here.
- **Shared-fixture contamination rule:** at most ONE mutation-granted lens on the sacrificial
  account at a time — stagger mutation lenses (or give each its own seed window); a concurrent
  observe lens mutating via direct API calls turns into a false P1 for its sibling.

## The five lenses (briefs for the `qa` agent prompt)
| Lens | Browser | Brief core |
|---|---|---|
| **user-flow** | yes | Walk the real user journeys (`<list your 2–4 core journeys>`). Hunt: dead ends, broken/missing back edges, context loss on refresh, a click that silently does nothing, navigation that contradicts your nav spec (if you keep one). |
| **edge-state** | yes | Force the unhappy paths OBSERVABLY (kill-API mid-session — coordinate with the integrator; slow network via devtools throttling; direct-URL deep links to foreign/absent ids; double-click where idempotency matters). Every state must be labeled, recoverable, and in user language. |
| **honesty** | no | Every NUMBER and claim on a screen (via its API payload) cross-checked against the store: counts, flags, states, terminal statuses. A screen asserting what the data does not support = P1. |
| **contract** | no | curl the public contract (`<where your API contract/types live>`): auth off / wrong account → uniform 401/403/404 (no existence leaks) · error bodies typed (machine `code` where the contract names one) · async 202s pollable to terminal states · malformed bodies → 400 with a client-safe message, never a 500 stack. READ endpoints first; mutations only on the sacrificial account. |
| **ux-critique** | yes | Screenshot the changed screens at `<your target widths, e.g. 1440 and 1024>`; judge against `<your design doc / tokens>` + neighboring-screen copy voice: hierarchy, spacing rhythm, truncation/overflow (long names/titles), empty-state quality, button affordance, copy-language consistency. Impressions allowed, but separate them from evidenced findings. |

## Findings format (the agent's final report, verbatim contract)
`id | severity P1/P2/P3 | screen-or-endpoint | expected | observed (verbatim) | repro steps | evidence`
then an «Impressions» list (unevidenced hunches), then ONE coverage line (walked / not reached).
Severity: P1 = a user is lied to, blocked, or sees dev language · P2 = a real journey degrades /
contract inconsistency · P3 = polish.

## Triage (integrator-owned)
1. Reproduce every P1/P2 by hand before it exists anywhere else (a report is INPUT — the
   fact-check rule).
2. Verified → a backlog ticket (or fold P3s into a standing minors batch); dropped → noted in
   the run record with the reason. Impressions may seed a design question, never a ticket
   directly.
3. Run record: `projects/<name>/qa/qa-run-YYYYMMDD.md` (lenses · scope · coverage · findings + verdicts ·
   tickets minted) + a row in § Runs. Screenshots stay OUT of git (reference by description).

## Calibration — how the lenses get BETTER
Three layers, cheapest first:
1. **Per-run meter (free, every run):** the run record captures precision
   (integrator-verified / total), cross-lens duplicate rate, evidence-completeness, and a
   coverage-honesty spot-check. Trend these across runs — a precision drop or duplicate rise is
   the drift signal. The one mechanism serious agentic-QA setups share is a human verifying
   every finding before it ships — that is exactly the integrator triage; keep it.
2. **Seeded-defect suite (the ground truth):** a VERSIONED, held-out list of 15–20 planted
   defects across the five lens classes (a lying counter · a dev string · a dead button · a
   stale-data path · a contract-shape break), mutation-testing style. Keep the registry
   OUTSIDE the repo so qa agents can never read it; plant on a throwaway branch, score RECALL
   per lens, revert. Agents must never see the list.
3. **Brief-iteration loop:** a missed defect class or a false-positive pattern → edit that
   lens's brief → re-run the seeded suite → keep the edit only on a recall delta. Found-before
   classes are the regression set (target ~100%; a drop = the brief broke). A lens that only
   duplicates other lenses' findings 3 runs straight is DROPPED. Start small — grow the suite
   from REAL verified findings, not invented hundreds.

LLM-judge note: triage is HUMAN (the integrator) — no judge calibration debt. If scale ever
forces an LLM triage judge: measure agreement against integrator labels on ≥50 stratified
findings first, judge from a different model family than the finder, and give it an «Unknown»
escape hatch.

## Optional extension — permanent regression specs (Playwright agent loop)
`npx playwright init-agents --loop=claude` scaffolds planner/generator/healer agent definitions
+ a `playwright-test` runner MCP in your web app's folder. Turn each verified repeat-regression
into a permanent spec (red-proof it: the spec must FAIL when the fix is removed), runnable
hermetically in CI. **Healer policy (house rule wins):** a failing test means the CODE is wrong
— the generated healer prompt leans toward «make the test pass», so use it ONLY under the
integrator; when a spec fails, fix the app (or skip with a documented «functionality broken»
note), never edit the assertion to green it. Regenerate the agent definitions when Playwright
updates.

## Runs
| Date | Scope | Lenses | Findings (verified/total) | Record |
|---|---|---|---|---|
