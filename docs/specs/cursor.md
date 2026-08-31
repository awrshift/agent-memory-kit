# Cursor — Tier 2 expected (manual checks pending)

Last verified: 2026-08-31, against Cursor 2.1.36 (macOS app; no `cursor`/`cursor-agent` CLI in
PATH on this machine). Cursor's plugin flow is in-app, so most of this spec is
`manual-check-needed` — the checklist below turns it into `verified`.

## What we could probe from a script (`verified`)

- Cursor 2.1.36 is installed; `~/.cursor/` contains `argv.json`, `extensions/`, `mcp.json` —
  no plugin/marketplace directories yet, so nothing about plugins could be probed headlessly.

## What the ecosystem documents (`documented-only`)

- Cursor installs Claude-format plugins natively via `/add-plugin` in the chat — the
  compound-engineering-plugin README lists Cursor among hosts that read a Claude-shaped
  plugin without conversion.
- Cursor auto-loads `AGENTS.md` (and its own `.cursor/rules/*.mdc`) as always-on context —
  which is the delivery path the kit's T2 protocol block relies on.

## Manual checklist (do once in the Cursor GUI, then update this file)

1. In Cursor chat: `/add-plugin` → add marketplace `awrshift/claude-memory-kit` → install
   `memory-kit`. Record whether the **nested** `plugins/memory-kit` source resolves.
2. In a fresh session, ask: "List the plugin skills available to you." Expect the 8
   `memory-kit` skills.
3. In a repo with an adopted `.claude/memory/MEMORY.md` containing a canary line and an
   `AGENTS.md` protocol block: ask the agent what it knows about the canary — this verifies
   the T2 chain (auto-load → follow → read memory), same probe that passed on Codex.
4. Note whether Cursor executes any of the kit's hooks (unexpected, but Codex surprised us by
   parsing `hooks.json`).

Move each item to `verified` with the observed result, and correct the tier in
`specs/README.md` if reality disagrees.
