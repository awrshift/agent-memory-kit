---
name: system-audit
description: "Periodic evidence-based self-audit of the whole agent system — the orchestrator, its docs/SSOTs, rules, memory, subagents, tools, infra and the work it claims to have delivered — followed by immediate cheap-safe fixes and a ranked backlog. Use when the user says 'аудит системы', 'проверь себя', 'самопроверка', 'system audit', 'audit yourself', 'health check', 'что у нас накопилось', 'система раздулась', 'проверь что работает а что на бумаге', 'gap-анализ', 'что удалить', or on cadence triggers (every ~10 sessions, before a milestone, after a big refactor, when memory hits its caps, when onboarding this repo to a new agent). Seven lenses: delivery reality · knowledge drift · operational layer · layer telemetry (did it ever fire) · tools & infra · domain gaps · anti-bloat subtraction. Not for reviewing a single diff (use a diff-review pass) and not for probing a running product (use /memory-kit:qa-sweep)."
---

# System audit — "what works / what drifts / what is missing / what to delete"

An agent system accretes. Good patterns and bad ones, dead rules nobody reads, facts restated in
five places with three of them stale, tools that only ran once. This skill is the periodic
sweep that keeps it **evolving without inflating**: it measures which layers actually fire,
deletes what doesn't, and reports findings that carry evidence rather than impressions.

**The one thing that makes this audit different from a checklist:** every claim must be backed by
something you touched with your own hands — a `file:line`, a command's output, a query result.
An unverified observation is labelled `hypothesis` and never counted in the verdict.

## Step 0 — Scope, depth, delta (2 minutes, always)

1. **Depth.** Pick from what the user asked, default `standard`:
   - `quick` — deterministic collector + lenses 1, 4, 7 inline, no subagents. ~10 min. Use for a routine "how are we doing", or when the user asks mid-work.
   - `standard` — collector + all 7 lenses, lenses 2-6 fanned out to parallel `recon` subagents (`model="sonnet"`), synthesis + adjudication inline. The default.
   - `deep` — standard + an independent architecture critique (`idea-validator`, `model="opus"`) and an external-family second opinion (`/memory-kit:second-opinion`), + a fresh-check of external facts (pricing, model ids, deprecated APIs) via WebSearch.
2. **Scope autodetect.** Run the collector (step 1) — it reports which layers actually exist in
   this repo. A lens whose layer is absent is reported as **n/a**, never invented. Never audit
   `node_modules/`, `.git/`, build output, or vendored code.
3. **Delta.** Read the newest prior report in `context/audits/` (or wherever it lives).
   For each of its priorities: **done · partially · ignored**. An audit whose last round was
   ignored has one finding worth more than all the others — say so first.

## Step 1 — The deterministic collector (before any reasoning)

```bash
# from the repo being audited; pass a path as $1 to audit a different repo
bash "${CLAUDE_PLUGIN_ROOT}/skills/system-audit/scripts/collect.sh" > /tmp/system-audit-facts.md
```

(If this skill lives somewhere else on your machine, run `scripts/collect.sh` from this skill's
own directory — it's read-only and never writes into the audited repo.)

For lens 4 (layer telemetry) also run the transcript profiler — it is the only source of
"did this ever actually fire", and it is read-only:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/system-audit/scripts/usage.py"
```

It parses this project's session transcripts and writes `knowledge/usage-frequency.md`: which
files, skills and tools were deliberately used (mechanical auto-loads and multi-edit bursts are
filtered out), and which have zero reads in 30 days. No transcripts yet → it says so and exits.

The main collector gathers, cheaply and repeatably: layer inventory · doc frontmatter coverage · memory caps ·
broken path references · git activity and cold files · secret exposure (gitleaks if present, an
`.env`-tracked check always) · **layer telemetry** (per rule/skill/agent: last mention in
session transcripts and in git history) · TODO/FIXME density.

Read its output first. It is the factbase; the lenses explain and prioritise it — they don't
re-derive it. Anything the script measured is a **fact**; anything a lens adds must earn its
own evidence.

## Step 2 — The seven lenses

Full briefs (what each lens checks, its evidence rules, its "n/a" condition):
`references/lenses.md`. Read it before dispatching.

| # | Lens | The question it answers |
|---|---|---|
| 1 | **Delivery reality** | Does the claimed state (backlog, handoff, README) match disk / git / prod? |
| 2 | **Knowledge layer** | SSOT hygiene: frontmatter, drift, the same fact restated stale in N places, contradictions between SSOTs. Standard: `reference/doc-governance.md`. |
| 3 | **Operational layer** | Rules, agents, memory, the self-improvement loops (findings registry → promotion → drop): coherent and non-contradictory? Standards: `reference/review-loop.md`, `reference/parallel-development.md`. |
| 4 | **Layer telemetry** | Which of those layers ever actually **fired**? Dead rules, never-invoked skills, agents defined once and never spawned. |
| 5 | **Tools & infra** | Reproducibility (pinned deps, a documented run path), secrets, backup **and restore**, ownership of external state. |
| 6 | **Domain gaps** | What a professional system *of this class* has and this one doesn't. The domain is named by the user or inferred; the lens brief lists gap-maps per common domain. |
| 7 | **Anti-bloat (subtraction)** | What to DELETE: never-fired layers, duplicated facts, ceremony with no consumer, over-engineering for a scale that never came. |

Dispatch rule for `standard`/`deep`: lenses 2-6 go to `recon` subagents **in one message** so
they run concurrently; each gets the collector output path, its brief verbatim, the repo root,
and the instruction *"return raw findings with file:line evidence; do not recommend architecture"*.
Lenses 1, 4 and 7 you run yourself — they need the whole picture and the authority to say "delete".

Model discipline: recon → `sonnet`; critique → `opus`; never pass the orchestrator model down.

## Step 3 — Integrator verification

An audit's only real product is trust in its findings, and that trust is exactly as strong as
the weakest unverified claim in it. So subagent reports are INPUT, not record. Before anything
enters the report:

- **Spot-check every load-bearing claim yourself** — open the `file:line`, re-run the command.
  Proportional to stake: a claim that drives a priority gets checked 100%.
- **Adjudicate disagreements on merits, never by vote count.** One dissenter holding a
  `file:line` outranks three abstract concurrences.
- Each disputed finding closes as **accepted (amended)** · **rejected WITH evidence** ·
  **deferred with a named verification step**.
- A finding you could not verify stays in the report marked `hypothesis` + the check that would settle it. Never silently dropped, never promoted to fact.

## Step 4 — Verdict, severities, priorities

Severity vocabulary (use these exact markers — they make audits comparable across time):

| | meaning |
|---|---|
| 🔴 | **broken** — a load-bearing thing does not work. Evidence attached. |
| 🟠 | **drifting** — works, but the doc/state/fact describing it is stale or contradicted. |
| 🟡 | **unverified** — a claim nobody has ever tested end-to-end (loops that never ran count here). |
| ⚪ | **missing** — a real gap for a system of this class. |
| 🗑 | **excess** — delete candidate. |

Then:

- **The verdict in three lines**: what works · what drifts · what is missing. Plain language, no hedging.
- **Max 5 priorities.** Each: `what · why now · cost (min/hours) · what breaks if we skip it`.
  A sixth priority is not a priority — park it in the backlog.
- **The subtraction quota is mandatory**: at least 3 🗑 candidates, or an explicit sentence
  saying the system is genuinely lean and why the telemetry supports that. An audit that only
  adds is a failed audit.
- **Cost honesty:** if a recommendation costs more than the pain it removes, say so and
  recommend against it. "Professional systems do it this way" is not a reason.

## Step 5 — Close the loop (this is what makes it evolution, not a ritual)

1. **Apply cheap-safe fixes immediately, in this session** — a stale path, a missing
   frontmatter line, an unpinned dep, a broken test. Announce each briefly. Anything with
   blast radius (deleting a rule, purging history, force-push) → ask first.
2. **Write the report**: `context/audits/audit-YYYY-MM-DD.md` (create the dir if absent) —
   template in `references/report-template.md`. It is the delta baseline for the next audit.
3. **Land the rest as tickets** in the project's backlog with its own id scheme — not as prose
   in the report where it dies.
4. **Feed the loops**: confirmed finding classes → the findings registry
   (`projects/<name>/review-findings.md`, or wherever that project's README maps it); a class on its 3rd occurrence → promote to the CHEAPEST layer
   that prevents it (deterministic check > agent/spec line > lens brief > knowledge article).
   Dead layers found by lens 4 → propose the drop.
5. **One line into MEMORY.md**, date-tagged: the audit's headline finding.
6. Tell the user: verdict, the 5 priorities, what you already fixed, what needs their decision.

## Cadence

Run it every ~10 sessions, before a milestone, after a large refactor, when memory trips its
caps, or when the user feels the system has bloated. Between runs, `quick` is cheap enough to
use as a pulse check. Two audits in the same week on an unchanged repo is itself over-engineering.

## What NOT to do

- **Don't report anything you didn't verify** as fact. `hypothesis` is an honest label; a confident
  wrong finding costs a real fix cycle.
- **Don't audit the code's business logic** — that is a diff-review pass (`/memory-kit:session-review` covers the session's diff); **don't probe the running
  product** — that is `/memory-kit:qa-sweep`. This audit is about the *system that produces the work*.
- **Don't propose a framework.** Prefer the smallest deterministic check that prevents a class.
- **Don't grade on aesthetics.** "Could be more structured" is not a finding. "This fact is
  stated three times, two of them wrong, here are the lines" is.
- **Don't skip the subtraction quota**, and don't delete a shared/rule/doc layer without the
  user's yes.
- **Don't let the audit itself grow.** If a lens has produced nothing actionable across three
  runs, drop the lens. The audit is subject to its own rules.
