# <slug> — assumed decision

**Created:** YYYY-MM-DD · **Status:** assumed · **Authorized by:** <who>, during <task>
**Parent spec:** `<path>`

> Written by an `executor` after an OWED DECISION and an explicit "build anyway". It is the only
> spec file an executor may create, and it never replaces the parent — it records what was
> assumed so the integrator can ratify or overturn it.

## Owed decision

The value that had no source in the parent spec, and the `AC-n` it serves.

## Assumption built on

The exact value or rule assumed, stated so someone else would build the same thing. Include the
candidates that were rejected and why this one was taken.

## Code area

Files and symbols that carry the assumption — where it must be changed if the ratification
lands differently.

## Ratify

The integrator deliberates this. Either it fills a real spec and this file is marked
`superseded`, or the assumption is confirmed and this file flips to `decided`. Until then it
stays flagged in session-start stats and in `code-sync`.
