# Postmortem — cue sheet

Blameless: roles and systems, never a person's name as a cause. Audience: whoever is on call the
next time this class of thing happens. Unproven cause stays a hypothesis, labelled.

---

# <YYYY-MM-DD> — <what broke, in the user's words>

**Status:** resolved | mitigated | ongoing · **Severity:** <how bad, by the project's scale>

## Timeline

Dated and timed, one line per event, from first symptom to resolution. Each line carries how it
is known: a log line, a commit, a message from the user, a monitor.

| When (UTC) | What happened | How it is known |
|---|---|---|
| YYYY-MM-DD HH:MM | <change deployed / job started> | commit `abc1234` |
| YYYY-MM-DD HH:MM | <first symptom> | <log, alert, user report> |
| YYYY-MM-DD HH:MM | <detected> | <who/what noticed, and how long after> |
| YYYY-MM-DD HH:MM | <mitigated> | <what was done> |
| YYYY-MM-DD HH:MM | <resolved> | commit `def5678` |

Gap nobody can reconstruct → one row saying so: `not verified — no record between HH:MM and HH:MM`.

## Impact

Who was affected, how many, for how long, and what they could not do. Numbers only with a source
(a query, a log count, a dashboard) — otherwise `scope not measured`.

## Root cause

The proven chain, each link with its evidence: trigger → mechanism → why the guardrails did not
stop it. Name the hunk or commit that introduced the mechanism, when the diff shows one.

Unproven link → write `hypothesis (not proven): <…>; would be confirmed by <the check>`.
Contributing factors go in their own short list, separate from the cause.

## What went right

Real, specific: the alert that fired, the rollback that worked, the test that caught the second
occurrence. This section is not decoration — it names the controls worth keeping.

## Action items

Each one owned, dated and small enough to finish. A vague item ("be more careful", "improve
monitoring") is not an action item.

| # | Action | Owner | By | Prevents recurrence / speeds detection |
|---|---|---|---|---|
| 1 | <change> | <role or name> | YYYY-MM-DD | prevents |
| 2 | <check> | | | detects |

## Findings registry rows to add

The finding CLASSES this incident confirmed, ready to paste into the project's
`review-findings.md` — this file proposes them; the integrator appends them.

```
| YYYY-MM-DD | <class-slug> | postmortem | <file or surface> | <AC-n or —> | <outcome> |
```
