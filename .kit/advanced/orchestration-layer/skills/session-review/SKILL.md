---
name: session-review
description: >-
  End-of-session adversarial review loop. Assemble the session's work into a role-assigned,
  self-contained brief, then run independent reviewers in parallel — an isolated code-reader
  (the idea-validator agent) that reads the ACTUAL files and web-checks technology currency,
  plus an external-family model if you have one — synthesize where they agree vs diverge,
  apply the cheap-safe fixes immediately, record a measurable plan for the rest, and CHALLENGE
  reviewer claims you disagree with (never blind-accept). Use at the close of a substantive
  coding or design session, when the user says "session review", "review my session",
  "stress-test this session", or types /session-review. Skip for trivial one-off edits.
---

# Session Review — the adversarial closing loop

Stress-test a session's work **before it sets**, using reviewers who don't share your blind
spots. You wrote the work, so you are the worst person to spot what you assumed. The loop ends
in *action*: cheap-safe fixes applied immediately, the rest recorded as a measurable plan, and
anything you disagree with explicitly challenged — not silently accepted, not silently dropped.

Invocation is usually EXPLICIT (`/session-review`) — "review" is something the agent does
natively, so don't expect auto-triggering; invoke it by name at session close.

## The loop

### 1. Assemble the brief (the load-bearing step)
Write ONE self-contained markdown brief (e.g. to `/tmp/<repo>-session-review.md`). It is the
only context the reviewers get. It must contain:
- **An assigned role** that fits the work ("Principal Engineer" for a feature slice, "Security
  reviewer" for auth work) — the role is the lens.
- **Project context** a stranger can follow, **the session goal**, and **what was built**, with
  concrete file:line references.
- **The specific decision points you most want challenged** — and for anything that turns on
  CURRENT best practice, an explicit ask to web-check with sources.
- **What to return** — a structured verdict with severity, file refs, a short MEASURABLE plan.

Never let the brief be the reviewer's only window: tell the code-reader explicitly
**"do not trust this summary — read the actual files."** Your summary is where your blind
spots live.

### 2. Run the reviewers IN PARALLEL (same message)
- **Reviewer A — the isolated code-reader.** Spawn `idea-validator` pointed at the brief AND
  the actual files, with the currency instruction: "web-check whether every library / runtime /
  pattern I chose is still the right choice this year, cite sources." Without that line it only
  verifies claims you explicitly made — dated tech slips through.
- **Reviewer B — an external-family model** (if available), reviewing from the brief only.
  Different training distribution, different blind spots; lean on it for concept and
  tech-currency, not file-level facts.
- One reviewer alone (A) is still a valid light review — note the absence and proceed.

### 3. Synthesize — agree vs diverge
Where reviewers independently land on the same finding — high-confidence signal, promote it.
Where they diverge — the highest-value rows: adjudicate on merits. On facts about the code the
code-reader wins; **never count votes**.

### 4. Act (the loop must end in action)
- **Accept now:** cheap, safe, low-blast-radius fixes — apply this session, verify by artifact
  (typecheck / lint / tests), don't round toward success.
- **Plan, measured:** larger items become backlog entries, each with a metric for the win.
  A plan item with no measurable outcome is a task for task's sake — drop it.
- **Challenge:** for anything you disagree with, write back WHY. Holding your ground with a
  reason is the partnership — blind acceptance defeats the loop.

### 5. Measure the outcome
Close with what the loop produced: findings found / applied / planned / challenged, what you
had missed, what tech-currency facts updated. That's how you know it earned its tokens.

### 6. Retrospective on the machine (so quality compounds)
Steps 1-5 review the WORK; this reviews the SYSTEM that produced it. Three questions, backed by
what actually happened this session:
- What foundation element (a rule, a MEMORY line, a handoff, a pattern) EARNED its keep —
  name the concrete moment. Keep those.
- Where did the foundation give friction or a gap — stale, duplicated, missing? Fix/merge/prune.
- How did the orchestration go — right agents, good-enough briefs, honest adjudication?

Output: at most 1-3 minimal, evidence-backed adjustments, biased to **subtract before add**.
"Keep doing" is a valid output — most sessions should change the foundation little.

## Guardrails
- Never blind-accept. Rejecting a finding with a reason is a success, not a failure.
- Separate "now" from "plan" by RISK, not importance — big-blast-radius changes at the end of a
  long session belong in the plan, done fresh.
- Scale to the work: small session → light brief, single reviewer; architecture change → the
  full role-assigned, fact-checked, multi-reviewer pass.
