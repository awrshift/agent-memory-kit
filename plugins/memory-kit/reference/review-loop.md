---
created: 2026-07-17
last-reviewed: 2026-10-22
---

# Review Loop — triage, the diff gate, the findings-class registry

> Three parts of one feedback loop: (0) every finding is triaged to the layer that owns it BEFORE it is written down;
> (1) every nontrivial diff passes an automated review before the integrator merges it; (2) every CONFIRMED finding is
> logged by CLASS and FAMILY, and a family that recurs three times is promoted into the strongest layer that prevents
> it. The loop is how review quality compounds instead of repeating itself.

## 0. Finding → decision (triage) — before anything is written down

Before a finding (a QA sweep, a code review, a reviewer round, something you read in an output) becomes a backlog row,
a status line or a fix list shown to the user, write ONE line for it:

`class (the mechanism that let it happen, not the symptom) · owning layer · owner`

- **Owning layer, strongest first:** data model (the defect cannot be represented) → boundary (rejected on entry) →
  deterministic check → prompt / instruction → review checklist. Pick the strongest one affordable now; a weaker pick
  is labelled «stopgap for <stronger layer>».
- **Owner** = an approved spec that already covers it, or NONE. Owner ≠ NONE → a line in that spec, not a ticket.
- **Group by family first:** findings that share one mechanism are ONE item.
- **History is not the current system.** A finding read from an old output is a defect of today's build only when no
  later change touched the same code; otherwise file it «old build — re-check on current».
- **Stop signal:** the 3rd fix round on one feature or one defect family → stop, write the general rule the cases share,
  show it to the user before round 4. A fix that names a specific input (a domain, a provider, a phrase) → ask which
  general property it violates.
- **Direction review:** the 3rd lever on one track that misses its pre-registered bar → review the DIRECTION, not the
  next spec: independent reviewers get the evidence files plus a list of what you suspect is weak in your own plan, then
  a free decisive check with bars written first.

## 1. The diff review gate

- Before the integrator merges a nontrivial diff (especially an executor branch), it passes an
  automated code review — e.g. Claude Code's `/code-review` — at **medium** effort.
- Escalate to **high** when the diff touches: a write path to real/user data · auth or
  security · paid spend · cached/derived determinism — and always before anything leaves your machine for another
  person's review (a PR, a release). (Adjust the trigger list to your project's risk map, but keep one.)
- Review findings are INPUT (see `orchestrator-fact-check.md`) — the integrator adjudicates
  each on merits before applying; never auto-apply, never count votes.
- Skip the gate for doc-only / trivial diffs — it's a gate, not a tax.

## 2. The findings-class registry (`projects/<name>/review-findings.md`)

One registry per project — the promotion rule counts occurrences of a FAMILY, and a shared file
across several projects makes that count meaningless. Already keeping one elsewhere? Leave it and
repoint the row in `projects/<name>/README.md`.

Every integrator-CONFIRMED finding from a code review, QA sweep, or design review appends ONE
row. Refuted findings are NOT logged — the ledger tracks real defect classes only. Counts are
derived by grep, never hand-tallied.

Row: `date · class-slug (family: <family>) · owning layer · found-by · where (file) · AC · outcome`

`AC` is the acceptance criterion the finding violates, `—` if none. **The family is mandatory**: most slugs occur once,
families recur (`grep -o "family: [a-z0-9-]*" review-findings.md | sort | uniq -c | sort -rn`).

```markdown
# Review-finding class registry
| date | class (family) | layer | found-by | where | AC | outcome |
|---|---|---|---|---|---|---|
```

**A family's count is not its escape rate.** Most rows are catches BEFORE shipping (your review, an executor, a lens).
What decides the next layer is how many rows were found AFTER shipping — by a user, a teammate, a downstream reviewer.
Write that in `found-by` so a grep can separate the two.

**Promotion — on a family's 3rd occurrence, move it to the STRONGEST layer that prevents it at acceptable cost**, and
mark the promotion in its row. Promote at sub-family granularity, or a coarse family never reaches a mechanical check:

0. the **data model / boundary** — the defect cannot be represented, or is rejected on entry. May fire on the 1st
   occurrence when an approved spec already owns that layer;
1. a **deterministic check** — lint rule / hook / grep gate (zero LLM context, fires forever);
2. a line in the relevant **agent definition** (`.claude/agents/*`), or a standing gate recorded
   in `projects/<name>/README.md` so every future spec inherits it — never an edit to the kit's
   own `SPEC-TEMPLATE.md`, which ships inside the plugin and is replaced on upgrade;
3. a line in a **review/QA lens brief** (`projects/<name>/qa/README.md`);
4. a `knowledge/concepts/` entry (last resort — knowledge nobody is forced to read is the
   weakest layer).

**The drop rule:** a promoted rule WITH a firing signal (a hook, a grep gate) that has printed no hit for ~5 sessions is
DROPPED. A checklist line prevents silently — no row is expected — so it is judged at a rules revision by its stake, not
by its hits. A registry that only grows becomes noise.
