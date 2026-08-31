# Codex CLI — Tier 2 (skills + AGENTS.md protocol)

Last verified: 2026-08-31, against `codex-cli 0.151.0` (npm `@openai/codex`), macOS, logged in
via ChatGPT. Probes ran real `codex exec` sessions.

## Install — no adapter needed (`verified`)

Codex reads the kit's **native Claude Code manifests** directly. The nested
`plugins/memory-kit` source in `.claude-plugin/marketplace.json` resolves correctly — no
root-native migration, no `.codex-plugin/` thin manifest required. Exact commands run:

```bash
codex plugin marketplace add awrshift/claude-memory-kit   # or a local path — both accepted
codex plugin add memory-kit@memory-kit
```

Result: `installed, enabled`; the whole plugin tree (skills, hooks, agents, templates,
reference, context) is copied to a versioned cache at
`~/.codex/plugins/cache/memory-kit/memory-kit/<version>/`. `codex plugin marketplace upgrade`
refreshes marketplace snapshots (`documented-only` — its own help text; not probed).

## What works (`verified`)

- **All 8 skills are visible in a live session**, namespaced `memory-kit:<name>` — probe asked
  a session to list its plugin skills; it returned `memory-kit:setup`, `memory-kit:close-session`,
  and the other six. Skill *descriptions* sit in session context, so auto-routing has something
  to match on.
- **`AGENTS.md` is auto-loaded and followed.** Canary probe: an `AGENTS.md` line instructing
  "read `.claude/memory/MEMORY.md` and quote its canary" was present in context AND the agent
  executed it, returning the canary from the memory file. This is the entire T2 delivery chain,
  confirmed end-to-end.

## What does NOT work (`verified`)

- **The SessionStart hook is not executed.** Codex *parses* `hooks/hooks.json` (it prints
  `warning: clamping SessionEnd hook timeout to 3s`), but a session started in a repo with an
  adopted `MEMORY.md` did **not** contain the canary — no injection, no hot cache in context.
  "Wakes up already knowing", the PreCompact block, and the protect-tests interception do not
  exist on Codex. The replacement is the protocol block `/memory-kit:setup` scaffolds into
  `AGENTS.md` (`templates/workspace/AGENTS-MEMORY-PROTOCOL.md`) — advisory, not enforced.
- Which hook events Codex *does* execute (the SessionEnd clamp suggests at least that one is
  wired) is `manual-check-needed` — irrelevant to the kit's guarantees either way.

## Notes

- Skill invocation syntax in Codex is `$skill-name` (`documented-only` — per the
  compound-engineering-plugin README); our probes exercised model-side auto-listing, not the
  interactive `$` form.
- `${CLAUDE_PLUGIN_ROOT}` does not exist on Codex. The hooks carry cwd/`__file__` fallbacks and
  the setup skill instructs path resolution relative to its own SKILL.md — no action needed.
- Real sessions require OpenAI auth; install mechanics (`plugin add`/`marketplace add`) work
  without it.
