---
created: 2026-07-17
last-reviewed: 2026-07-17
---

# Orchestrator fact-check — «a report is INPUT, never a source of record»

**Core rule:** anything produced by someone else — a subagent report, a reviewer verdict, a web
summary, model memory — is INPUT. It becomes a fact only after YOU touch reality at the
load-bearing point: run the command, read the file:line, query the store, open the raw
response. Proportional to stake.

## The three acceptance layers (all three before commit / user report / doc persist)

1. **Re-run objective gates YOURSELF** on the integrated tree — "tests green" in a subagent
   report is a claim, not a result.
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

## Adjudication (when reviewers/agents disagree)

- **Never count votes — adjudicate on merits.** One dissenter with a file:line beats three
  abstract concurrences; agreeing reviewers can share a blind spot.
- Rank by access: a repo-reading reviewer outranks a brief-only one on code facts; an
  external-family model outranks a same-family one on family-shared blind spots.
- Every disputed finding closes as: **accepted (amended)** · **rejected WITH EVIDENCE** ·
  **deferred with a named verification step**. "Verified" said to the user means you can name
  WHICH check you ran with your own hands.
