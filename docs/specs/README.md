# Platform specs

One file per agent host, recording **what that host can actually do with the kit** — verified
against the real tool, not its documentation. The pattern is borrowed from
[everyinc/compound-engineering-plugin](https://github.com/everyinc/compound-engineering-plugin),
which maintains an empirically-verified spec per foreign platform.

## Rules for a spec file

- **Header carries the evidence date:** `Last verified: YYYY-MM-DD, against <tool> <version>`.
  A spec older than a couple of host releases is a hypothesis — re-verify before relying on it.
- **Every claim is labeled.** Three labels, never omitted:
  - `verified` — we ran the command / probed the session; the exact command is quoted.
  - `documented-only` — asserted by the vendor's docs or a third party; never probed by us.
  - `manual-check-needed` — cannot be probed from a script; carries a checklist for a human.
- **Degradation is stated, not hidden.** If a host ignores hooks, say which guarantees die
  there and what replaces them (see the tier model in `../ARCHITECTURE.md`).
- A spec records **what is**, not what we wish; a failed probe is as much a result as a
  successful one.

## Current specs

| Host | Tier (see ARCHITECTURE) | Status |
|---|---|---|
| [claude-code.md](claude-code.md) | T1 — full enforcement | baseline, verified |
| [codex.md](codex.md) | T2 — skills + protocol | verified 2026-08-31 |
| [cursor.md](cursor.md) | T2 + verified SessionStart injection (T1-grade wake-up; other hooks unprobed) | verified 2026-08-31 (CLI) |
| [copilot.md](copilot.md) | T2 — skills + protocol | verified 2026-08-31 (CLI) |
| [agents-md.md](agents-md.md) | the T2 delivery convention itself | mixed |
