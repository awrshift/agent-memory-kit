---
created: 2026-10-22
last-reviewed: 2026-10-22
---

# Spec depth — the five lines a spec carries before anyone builds it

A spec (`templates/workspace/project/SPEC-TEMPLATE.md`) can be complete and still shallow: every field filled, the goal
met on paper, and the result wrong in the way experts in that field would have predicted. These five lines are what
the template's header asks for, and why. Each one exists because skipping it cost a real round of rework.

## 1. Depth pass — deeper, not bigger

Before a spec goes to a builder, a reviewer or the user, the designer runs one pass over it and writes the result into
the spec's own sections:

1. **What it is for** — the decision or event the work serves, and what the model needs to check its own result
   without a human (data access, a reproduction, a way to map a build to its change). No way to verify → say so first.
2. **What a top professional in this exact field would do that was not asked for** — the two or three moves that
   separate expert work from competent work here: the failure modes this kind of system is known for, base rates,
   reproduce before fixing, the counter-argument written out.
3. **The rawest material** — the data, logs, code, the official source; never a summary. A memory note, a handoff or a
   helper's report points at evidence; it is not the evidence. A claim about data holds over ALL rows, not one example.
4. **Methods and tools** — named techniques and why each fits.
5. **The check outside you and the model** — a test that fails without the change, a reproduction, ground truth, a
   held-out set, a measurement of the OUTCOME. A model judge is an ESTIMATE, not this check.

Keep the goal and the scope: every addition must lower the chance the result is wrong; one that only makes the job
bigger is dropped. The spec records it in one line — `Depth pass: <date> · <what changed>` or «nothing changed because
…». «Decided» means the design is chosen, not that the pass was run; a pass recalled from memory is not one.

Origin: Felix Rieseberg's depth prompt (felixrieseberg.com, 2026-10-13), packaged as a skill by DannyMac180/skills
(MIT), adapted with lessons from the maintainer's projects. If your user-level setup has its own depth skill, run that.

## 2. Practice — what the field does, checked now

`Practice: <file with sources and date>` or `not needed because …`. When a decision rests on something outside the
repository that can change or that the model only knows from memory — a version, an API's behaviour, a price, a
licence, a regulator's rule, «how the industry does X» — it is fresh-checked against official sources first, and the
dated result is filed (`projects/<name>/research/<topic>-YYYY-MM-DD.md`). Volatile facts (prices, versions, statuses)
expire after ~7 days; practices and standards after ~30. A spec value resting on an unchecked external claim is an
OWED DECISION.

## 3. Review — stake decides who reads it

`Review: <stake> · <why> · <who>`.
- **High** — the spec sets or changes the APPROACH: where a component sits, an irreversible data change (an enum value,
  a column, a backfill), state shared across processes, how a paid vendor is called, a scope proposal to the user →
  independent reviewers (`/memory-kit:second-opinion`, Boardroom), each asked to fresh-check every vendor claim.
- **Medium** — a build or fix round inside a decided approach → one code-reading reviewer.
- **Low** → self.
The depth pass raises the proof, never the approach; it does not stand in for the review.

## 4. Fail branches — written before the run

Per failure mode: what is tried next, and whose call it is — a redesign inside the approach (the agent) or a change to
what the user gets (the user). The branches cover every outcome, a mixed one included («both fire», «neither fires»).
The bar is not moved after the results are seen; a moved bar is a new version of the spec with its reason.

Before a PAID measurement (model calls, a vendor API, compute): a free count first — how many of the observed defects
the change can reach at all, and the limit it runs into — with the «not worth it» bar written before the count.

## 5. Measure the outcome, not a proxy

Acceptance is judged by what reaches the user. Agreement rates, gate passes, counters and model-judge scores are
reported as «screen only», never as the result: proxies have flipped sign once the outcome was measured. Every count in
a report comes from a saved script or command cited next to it; a hand tally is a draft until the script agrees.
