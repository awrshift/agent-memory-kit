# <Project name>

**Status:** active | paused | shipped | archived
**Started:** YYYY-MM-DD · **Last verified:** YYYY-MM-DD

One paragraph: what this project is, for whom, and what "done" looks like. No history —
history lives in the handoffs.

## Where this project's documents live

The map, and the only place that answers "where does a plan go". Paths are relative to THIS
folder unless they begin with `/`, which means the repository root (`/docs/plans/` is the repo's
own docs directory, `research/` is this project's). **If this repository already keeps a class of
document somewhere else, repoint the row instead of moving files** — the kit never relocates what
a repo already has.

| Class | Path | Written by |
|---|---|---|
| Tasks | `BACKLOG.md` | the integrator, continuously |
| Plans / specs | `plans/YYYY-MM-DD-<slug>.md` (from the kit's `SPEC-TEMPLATE.md`) | the main session, before building |
| Research + evidence | `research/<topic>-YYYY-MM-DD/` | `recon` sweeps, screenshot runs |
| Decisions ledger | `decisions-log.md` | the integrator, on a decision |
| Review-finding classes | `review-findings.md` | the integrator, on a CONFIRMED finding |
| QA protocol + runs | `qa/` — the protocol, plus one record per run | `/memory-kit:qa-sweep` |
| Client materials | `materials/` (briefs, PDFs, brand books) | the user drops them in |

Nothing above is scaffolded upfront: each path is created by whoever first produces that
artifact. An empty folder is not a layer.

**Not here** — these are shared across every project and stay at the repository root:
`.claude/memory/MEMORY.md` (hot cache) · `context/handoffs/` (session log) ·
`knowledge/` (deep memory) · `.claude/rules/` (hard rules) · `context/audits/`
(audits of the agent system itself, not of this project).

## Current state

2-3 sentences, replaced — never stacked. What is live, what is next, what is blocked.

## Pointers

- Live at: `<url or n/a>`
- Deploy / run: `<command or doc path>`
- External state this project owns: `<accounts, buckets, DNS zones — or "none">`
