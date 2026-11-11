---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# Measurement lessons — when a model reader may count, and seven ways a measure lied

> Read on demand, before you set a bar on a count or let a model's judgment decide a change. The general stance —
> measure the outcome, a model judge is an estimate, counts come from a script — is in `spec-depth.md` §1 and §5;
> this file adds the one exception to it and the lessons, each with the count that taught it.

## 1. The calibrated panel — the one exception to «a model judge is an estimate»

**Applies when:** the same judgment task (is this text on the brief, is this claim supported, which of two outputs is
better) recurs often enough that reading every item yourself is not an option.
**Take as is:** a panel counts only for its task: two model families, direct calls, order swapped, re-calibrated.
**Adapt:** the rubric and the models; the sample and the agreement bar may only rise — ≥ 30 items, ≥ 85 % are floors.

A panel's number counts as the measurement for THAT task only when all of these hold:

- **Readers from at least two model families**, called directly through the API — a fixed rubric, a constrained
  answer (yes / no, or a pick), the order of the two items swapped and a win counted only when both orders agree.
  Never an agent per read: an agent carries its system prompt, tool definitions and its own exploration into every
  turn; a direct call carries the rubric (cacheable) and the item.
- **Calibrated against your own blind labels** on at least 30 items of that task, with agreement of at least 85 %, both
  sides reported — what it caught and what it missed. Commit your labels to a file before you open the panel's answers.
- **Re-calibrated** when a panel model or the rubric changes. The panel never judges alone a text written by its own
  model family, and you still read at least one delivered output in full per run.

(one project's working practice; no count) Outside sources it rests on, as read 2026-10-23: a panel of smaller models
from disjoint families beat one large judge, with less self-preference (https://arxiv.org/abs/2404.18796); judges
prefer the first slot, the longer answer and their own family — swap the order, mix families
(https://arxiv.org/abs/2306.05685); grade with a model other than the generator and constrain its output
(https://platform.claude.com/docs/en/test-and-evaluate/develop-tests).

## 2. Seven lessons, each with its count and what the wrong measure had claimed

**Applies when:** you count or judge a system's output to decide a change — a classifier, a rule on model output, a
model reader, a bar on a counter.
**Take as is:** each lesson whose situation you meet — they are measured; the counts in them are one project's.
**Adapt:** the labelled rows (≥ 20 is a floor), the canary job and the control probe your paid runs need.

1. **Compare a classifier with the constant answer first.** The constant «verified» on every item agreed with the
   truth 50.4 % of the time, the live checker 54.4 % — while the constant caught 0 of 26 real conflicts. Agreement had
   said the checker worked; the measure became the pair «caught / spoiled».
   (measured in one project, 2026-09: 50.4 % vs 54.4 % agreement; 0 of 26 caught by the constant)
2. **A free count over stored data before a rule on model output.** An inventory of the instructions found 11
   conflicting rules; a free count over 71 stored outputs showed almost none reached the text (the one checked: 0 of
   71), while what the code did reached 71 of 71. The inventory had claimed eleven defects to fix. Another free count
   showed a planned change could reach 30 of 184 found defects against a bar of 25 % written before the count — the
   topic closed in an hour, with no paid run.
   (measured in one project, 2026-10 and 2026-11: 0 of 71 reached; 30 of 184 against a 25 % bar)
3. **A count that sorts items into a class reports its errors on at least 20 labelled rows before it is a bar.** A
   predicate marked 81 % of items «high-stakes» on any digit in them, and a bar was set on that number. Without the
   error count a sorting count is a screen, never a bar or a reason.
   (measured in one project, 2026-11: 81 % of items marked by the unchecked predicate)
4. **A pairwise read is a contrast, not an absolute measure.** Inside a paired read the reader's «publishable» verdict
   followed its pick: yes for the picked text 28 of 30, for the other 9 of 30. An edited version won every pair; read
   one text at a time on 16 topics, the publishable count was 2 before and 2 after, and 14 topics kept their grade.
   The pairs had claimed an improvement. Set bars on a single-item verdict.
   (measured in one project, 2026-11: 28 of 30 vs 9 of 30; 2 and 2 publishable on 16 topics)
5. **«Reached the text» by word match, and a bar on a counter, are screens.** «Reached the model» is not «reached the
   text», and «not copied verbatim» is a stand-in for the outcome — read before → after. A counter fell (repeats 11 → 2)
   while publishable texts went 1 → 2: the defect changed form. A length bar was met (5 of 52 refusals) while
   publishable texts fell from 7 of 10 to 3 of 8. The counters had claimed a fix.
   (measured in one project, 2026-10: repeats 11 → 2 with publishable 1 → 2; 7 of 10 → 3 of 8 with the bar met)
6. **A planted canary in every paid run.** One fixed, known job in each run, its mechanical outputs compared with its
   own earlier runs by script; plus one control probe the run must survive (pause and resume one job). The probe found
   a repeated charge after a resume on its first run, which neither the tests nor the review had seen — green tests had
   claimed nothing was broken.
   (measured in one project, 2026-10: one repeated charge found on the probe's first run)
7. **Give a model reader today's date.** Without it a reader called something «from the future» in 10 of 40
   replies, 9 of them about dates — false defects. The other side: a rubric reader saw 0 of 11 labelled wrong
   facts, and 4 of the 11 were stale only as of the text's date — staleness is invisible to a reader that does not
   know the date. Vendor guidance says the same for search tools: «also give it today's date» (checked 2026-10-07).
   (measured in one project, 2026-11: 10 of 40 false «future» calls; 4 of 11 wrong facts stale by date)

Related: `orchestrator-fact-check.md` (the history-window rule — a count from history carries its window and build) ·
`review-classes.md` (a heuristic's false-positive count) · `harness-measurement.md` (measuring the harness itself).
