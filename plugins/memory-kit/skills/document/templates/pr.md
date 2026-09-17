# PR body — cue sheet

Audience: the reviewer who will read the diff next. Facts, pointers, no warm-up paragraph.
Title: imperative, ≤ 72 chars, what changes — not "changes to X".

---

## Summary

2–3 lines: what this does · why now. The "why" comes from a commit body, the spec's Goal or the
user — none of those said it → `rationale: not stated`.

## Changes

One bullet per interface-visible or user-visible change, each with its file pointer. Internal
churn (renames, formatting, moves) collapses into a single bullet with a count.

- <what changed, in one line> — `path/to/file.py` (<the hunk in three words>)
- <…> — `path/to/other.ts`, `path/to/third.ts`
- <N files reformatted / renamed, no behaviour change> — `git diff --stat` says <N> files

## AC served

Ids from the governing spec's Acceptance table. Evidence = the hunk or commit that satisfies it.
No spec, or no matching AC → one line: `no spec — n/a`. Never invent an id.

| AC | Evidence |
|---|---|
| AC-1 | `path/to/file.py` — <what it now does> |
| AC-4 | commit `abc1234`; `wc -l` = 28 (ceiling 30) |

## How verified

Commands actually run, with their real output. Paste the result line, not a claim about it.

```
$ <command>
<the line that proves it>
```

Anything not run stays honest: `not verified — run <command>`. A failing or skipped gate is
listed here, not omitted.

## Risks / rollback

- Risk: <what could break, and where it would show first>
- Rollback: <revert commit / flag to flip / migration to reverse>
- Registered deviations from the spec, if any: <number, what, why>

Nothing risky → `low risk: <one line why>` (doc-only, additive, behind a flag).

## Out of scope

Straight from the spec's Non-goals plus anything a reviewer might otherwise expect and not find.
One line each, no apology.
