# QA layer (opt-in since v5.2)

Multi-lens **agent QA of your RUNNING product**: `qa` subagents probe the live app through five
independent lenses — user-flow · edge-state · honesty · contract · ux-critique — and return
structured findings with repro steps and machine-checkable evidence. The integrator reproduces
every load-bearing finding before it becomes a ticket. Distilled from the maintainers'
production practice (four calibrated sweeps in the first two days, including a seeded-defect
recall run).

Builds on the **orchestration layer** — enable that first: the whole harness rests on its core
invariant ("a subagent report is INPUT, never a fact").

## Why this shape

- **Lenses, not one "test everything" agent.** Each agent gets ONE adversarial angle and a
  verbatim brief. Narrow briefs find what a generalist skims past; a lens that only duplicates
  its siblings three runs straight gets dropped.
- **Evidence or it didn't happen.** Where a claim is machine-checkable, the finding must carry
  a `browser_verify_*` oracle result (Playwright MCP `--caps=testing`), not just a screenshot.
  Unevidenced hunches are labeled «impressions» and can never become tickets directly.
- **True parallel browsers.** A persistent Playwright profile can only be used by one browser
  at a time — so the layer runs each concurrent browser lens on its OWN `--isolated` MCP
  server (`mcp.json.example`). Two lenses, two servers, zero collision.
- **Honest empty results.** An empty findings table with a real coverage statement is a good
  result. Padding is the failure mode this layer is designed against.
- **It gets better on purpose.** The protocol ships a calibration ladder: per-run precision
  metrics → a held-out seeded-defect suite (kept OUTSIDE the repo so agents can't read it) →
  brief edits kept only on a measured recall delta.

## Enable

```bash
# from the kit root (orchestration layer already enabled)
mkdir -p .claude/agents docs/qa
cp .kit/advanced/qa-layer/agents/qa.md .claude/agents/
cp -r .kit/advanced/qa-layer/skills/qa-sweep .claude/skills/qa-sweep
cp .kit/advanced/qa-layer/PROTOCOL-TEMPLATE.md docs/qa/README.md
echo ".claude/qa/" >> .gitignore   # logged-in browser seeds live here, never committed
```

Then, in `docs/qa/README.md`, fill every `<placeholder>`: your app/API URLs and start commands,
the two-account policy (an observe-only real account + a sacrificial seeded one), your core
user journeys, and where your API contract lives. Merge `mcp.json.example` into your project's
`.mcp.json` and restart Claude Code so the `playwright-qa*` servers register.

An agent can perform this whole enable-and-fill sequence itself — point it at this README and
say "adopt the QA layer for this project".

## Contents

- `agents/qa.md` — the lens agent (observation-only, evidence rules, report contract)
- `skills/qa-sweep/` — `/qa-sweep`: preflight → pick lenses → spawn → integrator-verify →
  land tickets + a run record
- `PROTOCOL-TEMPLATE.md` — the protocol SSOT template (environment · account policy · the five
  lens briefs · findings format · triage · calibration ladder · the optional Playwright
  regression-spec loop). Copy to `docs/qa/README.md` and fill.
- `mcp.json.example` — the isolated, caps-enabled Playwright MCP server pair

## Hard rails (non-negotiable)

1. Real/demo accounts are OBSERVE-ONLY, always. Mutations happen only on a sacrificial seeded
   account, only when the run brief grants it, and only ONE mutation-granted lens at a time.
2. A finding becomes a ticket only after the integrator reproduces it by hand.
3. QA agents never see the seeded-defect registry.
4. A failing regression spec means the CODE is wrong — never green a spec by editing its
   assertion (the Playwright "healer" runs only under the integrator).
