# OpenCode — Tier 1: real injection via the shipped plugin

Last verified: 2026-08-31, against `opencode-ai 1.18.25` (npm), plugin SDK `@opencode-ai/plugin`
1.18.25, probes on `google/gemini-2.5-flash` via `opencode run`. Repo note: the OpenCode
project moved — `sst/opencode` now redirects to `anomalyco/opencode`.

## The mechanism (why this host is special)

OpenCode loads JS plugins in-process (Bun) and exposes a typed `Hooks` interface. There is
**no session-start hook**; our shim (`.opencode/plugins/memory-kit.js`) rides
`experimental.chat.system.transform`, which fires on **every model call** and lets a plugin
append strings to the system prompt. That is deliberately stronger than a one-shot injection:

- memory is re-read from disk per call — always current;
- it travels in the SYSTEM prompt, not the transcript — **compaction cannot drop it**, which
  makes Claude Code's PreCompact *block* unnecessary here rather than missing.

The shim also implements the caps check (180 / 32 KB / 3000, same numbers as the hook), the
unadopted-repo pointer (never scaffolds), skills registration, and a compaction nudge via
`experimental.session.compacting` (append-to-summary-prompt: "capture unsaved observations
into MEMORY.md right after compaction").

## Install (`verified` via the local-path form)

```jsonc
// opencode.json in the user's repo
{ "plugin": ["memory-kit@git+https://github.com/awrshift/agent-memory-kit.git"] }
// or a local checkout path: { "plugin": ["/path/to/agent-memory-kit"] }
```

The root `package.json` (name `memory-kit`, `main` → the shim) exists exactly for this
resolution and is covered by the CI version-agreement check. **Both forms `verified`
2026-08-31**: the probes below ran on the local-path form, and the git+ form was then probed
against live GitHub post-push — a fresh scratch repo with only `opencode.json` + a canary
`MEMORY.md` answered YES without reading a file.

## What works (`verified`, canary probes on 2026-08-31)

- **Injection**: in an adopted scratch repo, the MEMORY.md canary was present in the system
  context WITHOUT the agent reading any file, and the identity working agreement was there
  too. The core "wakes up already knowing" property holds — per call, not just per session.
- **All 8 skills available** — registered via `config.skills.paths` pointing at the plugin's
  `skills/` dir (the mechanism compound-engineering's own spec distrusted "until tested" —
  now tested). OpenCode also natively reads `.claude/skills/` and `~/.claude/skills/`, so
  user skills appear alongside.
- **The unadopted-repo guarantee**: a virgin repo got the one-line setup pointer in context
  and ZERO files created.
- OpenCode auto-loads `AGENTS.md` (and even `~/.claude/CLAUDE.md`) by itself
  (`documented-only`, its rules docs) — the T2 protocol block works here as a fallback even
  without the plugin.

## Degradation vs Claude Code (`verified` by API shape)

- **No compaction block.** `experimental.session.compacting` can only append context to the
  summarization prompt, not refuse it. Mitigated by the standing system-prompt injection
  (the cache itself cannot be lost) plus the capture-after-compaction instruction.
- **No test-edit guard yet.** `permission.ask` (allow/ask/deny) exists and could carry a
  protect-tests port — `manual-check-needed`, deferred until someone wants it.
- The relevant hooks are `experimental.*` — no API stability guarantee; re-verify on OpenCode
  upgrades. Pin: probes ran on 1.18.25.

## Notes

- Auth: any provider works; probes used Google via `GOOGLE_GENERATIVE_AI_API_KEY`.
- Skill invocation is by name (flat namespace) — identity.md's `/memory-kit:<name>` spelling
  maps to plain `<name>` here.
