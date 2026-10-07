# Security

## Reporting a vulnerability

Please report privately through GitHub: **Security → Report a vulnerability** on this repository.
Do not open a public issue for a security problem. Expect a first reply within a week.

Only the latest release is supported; fixes ship as a new version.

## What the plugin runs on your machine

Memory Kit has no server, no telemetry and makes no network calls. Its hooks are local Python and
shell scripts in [`plugins/memory-kit/hooks/`](plugins/memory-kit/hooks/), wired in
[`hooks.json`](plugins/memory-kit/hooks/hooks.json):

- **SessionStart** reads `.claude/memory/MEMORY.md`, the newest handoff and the knowledge index from
  your repository and prints them into the session context.
- **PreCompact** blocks compaction while `MEMORY.md` is stale or over its size caps.
- **PreToolUse** guards: asks before an edit removes or weakens a test assertion; blocks reads
  and writes of secret files (`.env`, `*.pem`, `id_rsa*`, …) and destructive git commands
  (`push --force`, `reset --hard`, `clean -f`, …). Each guard documents its opt-out variable.
- **SessionEnd** appends one timestamp line to `.claude/state/session-end.log`.

No hook writes your memory files. Scaffolding (`/memory-kit:setup`) runs only after you say yes;
during a session the agent writes memory entries itself and asks before adding a rule or a
knowledge article.
