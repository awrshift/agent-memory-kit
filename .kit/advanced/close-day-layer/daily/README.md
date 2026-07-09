# daily/

Chronological session logs, one file per working day: `daily/YYYY-MM-DD.md`.

**The agent writes these, not you.** They are the output of `/close-day` — the end-of-day audit ritual where the agent synthesizes what was said into a structured log and proposes promotions to `knowledge/concepts/` articles or `.claude/rules/` constraints.

Do not edit files here manually. If you want to add context or correct a log, say so in conversation — the agent will revise. Manual edits break the `/close-day` dedup check and the "user only talks" invariant.

During `/close-day` the agent distils these into topical articles in `knowledge/concepts/`. To search them, just ask the agent in conversation ("what did we decide about X?").

## Privacy

`daily/*.md` is gitignored by default — these are private working logs. Only `daily/.gitkeep`, `daily/README.md`, and `daily/TEMPLATE.md` are tracked. If you want to commit specific daily logs (e.g., for team handoff), opt in by adjusting `.gitignore` or `git add -f daily/<filename>.md`.

## Format

See `daily/TEMPLATE.md` for the structure `/close-day` produces.
