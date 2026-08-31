# GitHub Copilot CLI — Tier 2 (skills + AGENTS.md protocol)

Last verified: 2026-08-31, against `GitHub Copilot CLI 1.0.82` (npm `@github/copilot`), macOS,
authed via the GitHub CLI keyring login. Probes ran real `copilot -p` sessions.

## Install — no adapter needed (`verified`)

Copilot CLI's plugin system mirrors Claude Code's (`marketplace.json`-indexed GitHub repos;
its own help names skills, agents, **hooks**, MCP and LSP servers as plugin components).
Exact commands run:

```bash
copilot plugin marketplace add awrshift/agent-memory-kit
copilot plugin install memory-kit@memory-kit
```

Result: `Plugin "memory-kit" installed successfully. Installed 8 skills.` — the nested
`plugins/memory-kit` source resolved from our native `.claude-plugin/marketplace.json`;
`copilot plugin list` shows `memory-kit@memory-kit (v6.4.0)`.

## What works (`verified`, canary probes)

- **All 8 skills visible in a live session** — a `-p` probe listed close-session,
  memory-audit, qa-sweep, second-opinion, session-review, setup, system-audit, tour.
  Namespace is flat (no `memory-kit:` prefix observed), alongside the user's own skills.
- **`AGENTS.md` is auto-loaded and followed** — the same canary probe as Codex and Cursor:
  the instruction line was in context, the agent executed it, read `MEMORY.md` and returned
  its canary. The full T2 delivery chain holds.

## What does NOT work (`verified`)

- **The SessionStart hook is not executed** — in an adopted repo the MEMORY.md canary was NOT
  in context without reading (answer: NO). No injection, no "wakes up already knowing";
  the `AGENTS.md` protocol block from `/memory-kit:setup` is the replacement. Which hook
  events Copilot's plugin loader does run (its docs list hooks as a component) is
  `manual-check-needed`.

## Notes

- **Gotcha:** a stale `GITHUB_TOKEN` env var breaks auth with `401 Bad credentials` even when
  the keyring login is valid — clear it (`GITHUB_TOKEN= copilot …`), same discipline as `gh`.
- Two marketplaces ship by default (`github/copilot-plugins`, `github/awesome-copilot`);
  Copilot also loads `.github/skills` and `.github/agents` from `--add-dir` directories
  (`documented-only` — its own help text).
- Non-interactive runs need `--allow-all-tools` and consume Copilot AI credits (a paid
  GitHub Copilot plan).
