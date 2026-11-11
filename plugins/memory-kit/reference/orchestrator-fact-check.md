---
created: 2026-07-17
last-reviewed: 2026-11-11
---

# Orchestrator fact-check — «a report is INPUT, never a source of record»

**Core rule:** anything produced by someone else — a subagent report, a reviewer verdict, a web
summary, model memory — is INPUT. It becomes a fact only after YOU touch reality at the
load-bearing point: run the command, read the file:line, query the store, open the raw
response. Proportional to stake.

## The three acceptance layers (all three before commit / user report / doc persist)

1. **Re-run objective gates YOURSELF** on the integrated tree — "tests green" in a subagent
   report is a claim, not a result.
   Keeping that run as a receipt bound to the accepted tree is an option under trial in one project — it changes how
   the run is recorded, not this layer: `acceptance.md` §5.
2. **Eyeball one REAL end-to-end artifact** and exercise the primary user scenario — metrics
   aggregate; eyes catch what aggregation hides.
3. **Spot-check the load-bearing claims** of any factbase or review against the source
   YOURSELF before persisting or acting on them.

## Claim classes → the cheapest decisive check (< 2 min each)

| Claim | Check |
|---|---|
| «X exists / behaves like Y» | Read the file:line yourself; grep the symbol |
| «Count / state in data is N» | One query against the real store |
| «Cost / pricing / limits» | ONE raw API response or the official page, quoted verbatim |
| «External state» (PRs, deploys) | A live CLI/API call; anything >7 days old is a hypothesis |
| «Gate passed» | Re-run it yourself |
| «Model/library still works like X» | Official source or one live probe — never model memory |
| «A model judge scored it N» | An ESTIMATE, never the check; the one calibrated exception: `measurement-lessons.md` |
| «The system does N / fails with X» from history | See the history-window rule below |

## A statement carries its check

**Applies when:** you tell the user how the code, the data or a run is NOW, or act on a premise someone handed you.

- **A statement about the current state travels with the command or the file line that checked it**, in the same
  message. A queue line, a handoff, a memory entry and a comment in code are pointers, not the check. In one project
  this rule already existed and still did not fire on three dates running: a task taken from a queue line without
  opening its plan (a paid run planned that a newer decision had ruled out, stopped before the spend), a defect's
  cause named without the stored trace of the run, and «off by default» said before anyone searched where the switch
  is read — it was on (measured in one project, 2026-11: three dates in a row).
- **A premise is checked before it is acted on.** A premise from the integrator about code, data or a run is checked
  by whoever acts on it, first; a wrong one goes back in the next message with its evidence
  (one project's working practice; no count).
- **A ruling that rests on a mechanism quotes the line and names what reads it** — «setting X decides Y» quotes the
  line's text and names the code path that reads that line. In one project's retro, four of five wrong claims cited or
  remembered a line without the path that reads it (measured in one project, 2026-11: 4 of 5 wrong claims).

## The history-window rule

Accumulated history — a DB, logs, past runs, a ledger — mixes many builds and many days.

- A number or an error pulled from it is stated **with its time window and the build/version
  that produced it**: «41 of 120 articles failed (2026-09-20..25, engine builds 1.4.0–1.4.12)».
- A present-tense claim about the CURRENT system («the engine fails on X», «billing is broken»)
  is checked on current data only — filter to the latest build or reproduce it now.
- **Date an error before describing it.** A three-day-old failure reported as live sends
  everyone after a bug that may already be fixed.

## Adjudication (when reviewers/agents disagree)

- **Never count votes — adjudicate on merits.** One dissenter with a file:line beats three
  abstract concurrences; agreeing reviewers can share a blind spot.
- Rank by access: a repo-reading reviewer outranks a brief-only one on code facts; an
  external-family model outranks a same-family one on family-shared blind spots.
- Every disputed finding closes as: **accepted (amended)** · **rejected WITH EVIDENCE** ·
  **deferred with a named verification step**. "Verified" said to the user means you can name
  WHICH check you ran with your own hands.
