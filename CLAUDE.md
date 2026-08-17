# Working on Memory Kit

This repo is a **Claude Code plugin marketplace**, not a memory workspace. The plugin lives in
`plugins/memory-kit/`; `.claude-plugin/marketplace.json` is the catalog. Users install it into
*their* repositories — nothing here should assume it runs at the project root.

## Rules that are easy to get wrong

- **Paths.** Anything the plugin ships resolves from `${CLAUDE_PLUGIN_ROOT}`; anything about the
  user's repo resolves from `CLAUDE_PROJECT_DIR`. Never derive a project root from `__file__` —
  the plugin runs from a cache directory.
- **Never write into a repo that didn't ask.** The plugin can be installed user-wide. Scaffolding
  happens only inside `/memory-kit:setup`, after a yes.
- **What a plugin cannot ship:** `CLAUDE.md`, `.claude/rules/`, and any `settings.json` key other
  than `agent` / `subagentStatusLine`. Context therefore travels via hooks, skills and agents —
  the working agreement is `plugins/memory-kit/context/identity.md`, injected at SessionStart.
- **Always-loaded vs on-invoke.** A skill body loads only when invoked; a rule without `paths:`
  loads every session forever. Put weight in skills and `reference/`, never in rules.
- **Verify injection by looking at the context, not the code.** v5 claimed for a year that the
  hot cache was always loaded while the hook only measured it. Run the hook and read its output.

## Before committing a change to hooks or skills

```bash
claude plugin validate ./plugins/memory-kit
CLAUDE_PROJECT_DIR=<test-repo> CLAUDE_PLUGIN_ROOT=$PWD/plugins/memory-kit \
  python3 plugins/memory-kit/hooks/session-start.py <<< '{"source":"startup"}'
```

Exercise every SessionStart `source` (startup · resume · compact · fork · clear) and both hook
outcomes for `protect-tests.py` — the profiles are the whole design, and a broken one fails
silently.

## Docs that must stay true in the same commit

A behaviour change touches `docs/CHANGELOG.md`; a layer change also touches `docs/ARCHITECTURE.md`
and the README's skill table. `VERSION`, `plugin.json` and `marketplace.json` carry the same
version — they have drifted before.

## Language

Docs, code and commits in English. Conversation with the maintainer in Russian.
