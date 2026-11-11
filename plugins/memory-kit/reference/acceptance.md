---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# Acceptance — the record a block of work is accepted on

**Applies when:** you accept a helper's or another session's build after at least one review round.

The kit already says the three acceptance layers (`orchestrator-fact-check.md`) and that a fix round's diff is
reviewed like any diff (`review-loop.md` §1, with the counts behind it). This file adds the RECORD that makes both
checkable after the fact, the bounds that keep a fix round from turning into a redesign loop, and one option for the
gates under trial. The file to copy: `templates/workspace/project/ACCEPTANCE-TEMPLATE.md`.

## 1. The record — one file per accepted block

One file in the block's plan folder, written by the integrator at acceptance, committed with the acceptance
(in trial in one project since 2026-11-10; count due at its next six block acceptances):

- `Head:` the exact commit accepted, full hash. Accepting means accepting THAT tree, not the branch name.
- `Spec:` the path and its version (`v<N>`). A redesign changes the version (§4).
- `Rounds:` the number of fix rounds after the build.
- `Fix-diff review: <build head>..<fix head> — <record path>` — or, with no fix round, `Build review: <base>..<head> —
  <record path>`. The range ends at `Head:`; the record is a committed file written after that head.
- `Gates:` what ran on that tree and its result — your own re-run (the default) or a receipt (§5).
- `## Findings decided` — exactly one ruling line per finding id of the review record: accepted (amended) · rejected
  with evidence · deferred with a named check, or a ticket. A finding without a ruling is an open finding.
- `## Other tops` — only when work is held in parallel: `parallel-development.md` «Held work drifts».

Why a file and not a sentence in a report: the review half (the range reviewed, who reviewed it, the ruling on each
finding) is what a later reader cannot reconstruct from git, and an acceptance said in chat is gone at the next
session. A short script can check the record at the acceptance commit: the head resolves, the review record contains
the range and was committed after the head, every finding id has one ruling. That check proves the record EXISTS —
not that the review was good (§6).

## 2. The fix-diff review asks one more question

The reviewer — an agent that did not write the fix — reads `<build head>..<fix head>` against the fix spec and answers,
besides its findings: «which mechanisms does the diff add that the fix spec does not name (a new function, predicate,
rule set, table)?». Its record has a heading for that list; «none» is a valid answer. Where the fix spec carries a
layer line (`review-loop.md` §0), the reviewer reads the diff BEFORE that line and answers «agree» or «disagree — why»;
a disagreement is ruled in `## Findings decided`
(in trial in one project since 2026-11-10; count due at its next six block acceptances).

## 3. «Blocking», defined before the round

A finding of a fix-diff review is **blocking** when it breaks one of the round's bars, reopens a defect class the round
was opened for, or breaks an acceptance criterion of the block's spec that held at the build head. A defect that changes
what the user (or the user's customer) is charged or gets goes to the integrator first, whatever its size. Anything
else becomes a ticket, not a further round (in trial in one project since 2026-11-10; count due at its next six block
acceptances).

Why a bound: without one, every review of a fix finds new items and every fix adds a defect. In one project, in the unit
whose every fix diff was reviewed, each review of a fix found about ten items and the loop ran seven rounds before the
integrator froze it; over all six units the fix commits made 34 blocking defects in 36 commits, about one each
(measured in one project, 2026-11: 34 defects made by 36 fix commits).

## 4. A fix round may not redesign

The integrator rules on each mechanism of §2's list in `## Findings decided`: kept as part of the fix, or the round
stops and the redesign becomes a new spec version, read before its build (`spec-depth.md` §3) — never built inside the
fix round (in trial in one project since 2026-11-10; count due at its next six block acceptances).

Why: of 72 blocking findings of later rounds in one project, 35 sat in code that a fix round had redesigned and 34 were
made by a patch meant to fix a listed item; 3 had been in the first build and missed by its review
(measured in one project, 2026-11: 35 of 72 in redesigned code). The rounds come from the fixes, not from the first
review's recall.

## 5. The gates as a receipt — an option under trial

The kit's layer stays: the integrator runs the objective gates itself on the tree it accepts
(`orchestrator-fact-check.md` layer 1). This option changes HOW that run is kept, not who trusts it.

A script runs the project's full gate set once in a clean worktree at the head to accept and writes a receipt
(one JSON file): the head and its tree hash, `git status --porcelain` before AND after the run (untracked files
included), per gate the exact command, the exit code or «timeout», start and end time, and the counts read from the
test runner's machine-readable report — plus a hash of the receipt's own content. The acceptance names it in `Gates:`,
and the acceptance check refuses:

- a receipt for another tree than `Head:`'s, or a tree that was dirty before or after the run;
- a gate whose recorded command differs from the script's constant, or a mandatory gate skipped;
- a suite of 0 files or 0 tests — a vacuous pass (the general rule, a check fails on an empty subject:
  `project-extensions.md` «Telemetry»);
- a failed or timed-out gate without a written line `Gate ruling: <gate> — <why>` by the integrator;
- a skippable gate skipped without a reason.

Why: one project re-read its eight acceptance files. The gates had been re-run by hand in seven, all green; in two the
re-run was on another head than the one the window's count or the acceptance refers to, and in the eighth the re-run was
skipped and only a prose line said so (measured in one project, 2026-11: 2 of 7 hand re-runs on another head). What a
receipt closes is the honest error — another head, half the gates, a result from memory; a deliberate forgery is outside
it (in trial in one project since 2026-11-11; count due at its next six acceptances: hand re-runs, wrong refusals).

Until your own count says otherwise, run the receipt script yourself — a receipt a helper wrote and you did not
check is a helper's «green» in another format.

## 6. What decides whether this works

Every check above counts the record being written — a screen. The outcome is whether accepted fix code still
carries blocking defects: a fresh blind review of a few accepted fix diffs, drawn after a fixed number of
acceptances, that finds none the integrator confirms. In one project the record and the receipt have not yet reached
that count (one project's working practice; no count).
