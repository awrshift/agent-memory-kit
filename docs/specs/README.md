# Claude Code specs

The kit runs in one host, Claude Code. `claude-code.md` records **what Claude Code actually does
with the kit** — verified against the real tool, not its documentation.

## Rules for a spec file

- **Header carries the evidence date:** `Last verified: YYYY-MM-DD, against <tool> <version>`.
  A spec older than a couple of host releases is a hypothesis — re-verify before relying on it.
- **Every claim is labeled.** Three labels, never omitted:
  - `verified` — we ran the command / probed the session; the exact command is quoted.
  - `documented-only` — asserted by the vendor's docs or a third party; never probed by us.
  - `manual-check-needed` — cannot be probed from a script; carries a checklist for a human.
- **Degradation is stated, not hidden.** If a Claude Code release stops honouring a mechanism,
  say which guarantee dies and what replaces it.
- A spec records **what is**, not what we wish; a failed probe is as much a result as a
  successful one.

## Current specs

| File | Status |
|---|---|
| [claude-code.md](claude-code.md) | baseline, verified |

The specs for Cursor, Codex, Copilot CLI, OpenCode, Cowork and `AGENTS.md` were removed in 8.0,
when the kit became Claude Code only; they remain in git history at tag `v7.3.0`.
