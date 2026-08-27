# Review Loop — the diff gate + the findings-class registry

> Two halves of one feedback loop: (1) every nontrivial diff passes an automated review before
> the integrator merges it; (2) every CONFIRMED finding is logged by CLASS, and a class that
> recurs three times is promoted into the cheapest layer that prevents it. The loop is how
> review quality compounds instead of repeating itself.

## 1. The diff review gate

- Before the integrator merges a nontrivial diff (especially an executor branch), it passes an
  automated code review — e.g. Claude Code's `/code-review` — at **medium** effort.
- Escalate to **high** when the diff touches: a write path to real/user data · auth or
  security · paid spend · cached/derived determinism. (Adjust the trigger list to your
  project's risk map, but keep one.)
- Review findings are INPUT (see `orchestrator-fact-check.md`) — the integrator adjudicates
  each on merits before applying; never auto-apply, never count votes.
- Skip the gate for doc-only / trivial diffs — it's a gate, not a tax.

## 2. The findings-class registry (`projects/<name>/review-findings.md`)

One registry per project — the promotion rule counts occurrences of a CLASS, and a shared file
across several projects makes that count meaningless. Already keeping one elsewhere? Leave it and
repoint the row in `projects/<name>/README.md`.


Every integrator-CONFIRMED finding from a code review, QA sweep, or design review appends ONE
row. Refuted findings are NOT logged — the ledger tracks real defect classes only. Counts are
derived by grep, never hand-tallied.

Row: `date · class-slug · found-by · where (file) · outcome`

```markdown
# Review-finding class registry
| date | class | found-by | where | outcome |
|---|---|---|---|---|
```

**The promotion rule — on a class's 3rd occurrence, promote it to the CHEAPEST layer that
prevents it, and mark the promotion in its row:**

1. a **deterministic check** — lint rule / hook / grep gate (zero LLM context, fires forever);
2. a line in the relevant **agent definition** (`.claude/agents/*`), or a standing gate recorded
   in `projects/<name>/README.md` so every future spec inherits it — never an edit to the kit's
   own `SPEC-TEMPLATE.md`, which ships inside the plugin and is replaced on upgrade;
3. a line in a **review/QA lens brief** (`projects/<name>/qa/README.md`);
4. a `knowledge/concepts/` entry (last resort — knowledge nobody is forced to read is the
   weakest layer).

**The drop rule:** a promoted rule that stops firing for ~5 sessions is DROPPED — same
unique-value discipline as review lenses. A registry that only grows becomes noise.

Related classes are worth naming as a FAMILY in the row (e.g. three different "a bound
silently hides content" findings in one day) — the family, not the instance, is what earns a
promotion.
