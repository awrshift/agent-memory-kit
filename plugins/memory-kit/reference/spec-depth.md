---
created: 2026-10-22
last-reviewed: 2026-11-13
---

# Spec depth — what a spec carries before anyone builds it

A spec (`templates/workspace/project/SPEC-TEMPLATE.md`) can be complete and still shallow: every field filled, the goal
met on paper, and the result wrong in the way experts in that field would have predicted. These lines are what
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

**Before the build, a reader who did not write the spec reads it** — the prebuild reader. It reads against the code at
the spec's base commit (every premise about existing code, schema or migration opened there, not recalled) and
against itself (two lines that cannot both hold). Findings go into a committed file, one id each; the integrator rules
on EACH before the build — fixed in the spec (with the new commit) · rejected with evidence · deferred with a named
check — and the build starts only when every id has a ruling. One project makes it a line of every build brief; it
is mandatory when the mechanism is a queue, a ledger or a lock. **No third read of one spec:** when the second read
still finds a lot, its findings are classed by cause first (a wrong statement about existing code, or an under-defined
new rule); a pile of the second kind means the deciding rules need a case table (§6), not another read. In one
project three reads of one spec found 28 → 22 → 29 items: wrong statements about code fell from 11 to 7 while
under-defined new rules rose from 7 to 16 (measured in one project, 2026-11: three reads of one spec). The role template: `prebuild-reader`
(`helper-roster.md`). Why: on one project's queue-and-lock designs the spec read changed the approach on three dates
within five days; on six later units, a check before the build could have shown a first-round defect in two, and
both catches were such reads: a library fact sitting in the project's own code at the base commit, and two spec
lines that contradicted each other — one shown, one argued; in none would it have saved a round (measured in one
project, 2026-10 and 2026-11: 3 approach changes; 2 of 6 units).

## 4. Fail branches — written before the run

Per failure mode: what is tried next, and whose call it is — a redesign inside the approach (the agent) or a change to
what the user gets (the user). The branches cover every outcome, a mixed one included («both fire», «neither fires»).
The bar is not moved after the results are seen; a moved bar is a new version of the spec with its reason.

Before a PAID measurement (model calls, a vendor API, compute): a free count first — how many of the observed defects
the change can reach at all, and the limit it runs into — with the «not worth it» bar written before the count.

**Paid runs.** The spec carries «N units, ~cost, cap» BEFORE the run. The estimate comes from a script over measured
rows, never from memory or a number quoted from a report; the run script reads the cap from the spec and stops itself at
it (a cap that counts past spend gets spent + this run's budget). **One money line, set by the user:** below it the
agent decides and reports the actual cost after; above it the user approves EACH run on one line — «N units, ~cost,
cap, why» — even when the plan holding the run was approved. A part whose run depends on an earlier part's bar is paid
only after that bar is scored. Every parameter of a paid run has a written source: the project's coverage plan, or
chosen for this task with its reason (one project's working practice; no count).

**The launcher, the dry run and the key probe — shown before the yes.** A paid step is started by a COMMITTED script
that loads the environment (keys, endpoints, slot settings) inside itself; nobody types a key or exports one by hand,
and a command that reads a key out of an environment file is refused by the deny rules. Before the money line's yes,
the stop shows two free outputs: the launcher's **dry run** — the whole path up to the vendor call, with the units, the
estimate and the cap it will use, no call made — and a **probe of every vendor key** the run will call (one zero-cost
request per key: a model list, an account balance). The approver approves a command it has seen, and a depleted or
refused key is found before the paid step, not inside it. Why: in one project a spend was approved whose launch
command main had not seen, and the step stopped inside the window; another run found its primary key empty mid-run
(one project's working practice, 2026-11; no count).

**The money line, written down.** One table in the project's rules: who approves which cap. A typical shape — a cap
up to a small sum is the integrator's call and the user is told the actual cost after; above it the user's yes on one
line «N units, ~cost, cap, why» before EACH run; a window never spends without main's yes on its brief's paid line,
and main's yes never stands in for the user's above the line. Plan · approved · actual per run go into a dated spend
sheet the user sees at the close (one project's working practice; no count).

## 5. Measure the outcome, not a proxy

Acceptance is judged by what reaches the user. Agreement rates, gate passes, counters and model-judge scores are
reported as «screen only», never as the result: proxies have flipped sign once the outcome was measured. Every count in
a report comes from a saved script or command cited next to it; a hand tally is a draft until the script agrees.
Which numbers are screens and which are measurements — the constant-answer baseline, a count proven on labelled rows,
the one calibrated exception to «a model judge is an estimate»: `measurement-lessons.md`.

## 6. Deciding rules — a function with a case table, not prose

**Applies when:** the spec holds a rule that decides on cases — keep or drop, retry or stop, which branch, which label.

A spec carries a line `Deciding rules: none — <why>` or `Deciding rules: <path of the case table>`. Per rule:

- **the function's name and signature** — the rule is code from the first slice, not a paragraph;
- **a case table** — literal inputs, the expected decision and its reason, one row per outcome;
- **the writer of each input** — the code path or data source that can actually produce that literal; an input no
  writer produces is not a case (its boundary is tested once);
- **the command that runs the table** — the table is a test that runs, accepted by its exit code, never by reading.

```
rule: should_retry(status, attempt)            run: <test command> -k should_retry
| status | attempt | expected        | reason                       | writer that produces it  |
| 429    | 1       | retry           | rate limit is transient      | vendor client, on 429    |
| 429    | 3       | stop: give_up   | the retry budget is 3        | vendor client, on 429    |
| 400    | 1       | stop: refuse    | the request itself is wrong  | vendor client, on 4xx    |
| None   | 1       | stop: error     | no status = transport failed | the timeout path         |
```

**Proven by an exhaustive run, with planted breaks.** Where the inputs are small (a few enums, small integers), the
build runs the function over EVERY combination and checks each result against the rule's invariant stated first
(«never retry a 4xx other than 429», «never more than N attempts»), not only the listed rows. Then it plants a break —
flips one branch, shifts one boundary by one — and shows the run catches each one; a planted break the run does not
catch means the invariant or the table is too weak. The deciding functions are the build's FIRST slice; the
measurement that depends on them runs on the built functions. Prose stays for the wiring only, and there every
statement about existing code is a row «claim · file:line opened at the build's head».

Why: in one project the share of prebuild findings that were under-defined or wrongly deciding NEW rules rose across
three reads of one prose spec (7 → 16), while the spec kept growing; a table that runs ends that loop (§3; measured
in one project, 2026-11: three reads of one spec). The rule is in trial: one project's count of reads per spec after
the change is due 2026-11-25.
