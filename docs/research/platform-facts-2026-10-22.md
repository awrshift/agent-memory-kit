---
created: 2026-10-22
last-reviewed: 2026-10-22
status: current
authority: ssot
---

# Platform facts — fresh-check 2026-10-22 (for the 7.3 fixes)

Official sources only, fetched 2026-10-22; the quotes are verbatim. Volatile: re-check after ~30 days or a host release.
Claude Code on this machine: 2.1.308.

## Claude Code — hooks (`https://code.claude.com/docs/en/hooks.md`)

| Fact | Quote | Used by |
|---|---|---|
| Hook output cap | "A hook's `additionalContext`, `systemMessage`, and `initialUserMessage` strings, and its plain stdout, are capped at 10,000 characters" · over it Claude gets "the file path with a preview of up to the first 2,000 characters" · "this cap has no setting or environment variable to raise it" | session-start parts; `reference/project-extensions.md` |
| PreCompact blocking | "If compaction was triggered proactively before the context limit, Claude Code skips it and the conversation continues uncompacted. If compaction was triggered to recover from a context-limit error already returned by the API, the underlying error surfaces and the current request fails." Matchers: `manual` (`/compact`), `auto` (auto-compact window and idle compaction) | pre-compact.sh (7.3: block `manual` only) |
| PreCompact / PostCompact output | "Claude Code discards a PreCompact hook's `systemMessage` and `continue` fields." PostCompact: "no decision control"; it receives `compact_summary` | why the post-compaction nudge rides SessionStart `compact` |
| Fail-open default | "On most events, when a hook fails or times out, Claude Code still carries out the action. A policy hook with a wrong path or a crashing script then lets everything through. To block the action instead, set `"onFailure": "block"` on a `command` or `http` hook. Requires Claude Code v2.1.295 or later." Failures: can't start · exit other than 0 or 2 · timeout · invalid output | guard-secrets, guard-git |
| SessionEnd budget | "SessionEnd hooks share a 1.5-second budget; if your settings set a longer per-hook `timeout`, Claude Code raises the budget to match, up to 60 seconds" · "Timeouts set on plugin-provided hooks don't raise the budget." | session-end hooks.json timeout |

## Claude Code — plugins, memory (`code.claude.com/docs/en/plugins-reference`, `/memory`)

- A plugin's `settings.json`: "Only `agent` and `subagentStatusLine` take effect; other keys are dropped at load." A
  `CLAUDE.md` at the plugin root is not loaded. The plugin layout has no rules directory.
- "Rules without a `paths` field are loaded unconditionally"; a path-scoped rule loads on Read/Write/Edit of a matching
  file, or a single-file `cat`/`head` (fixed in 2.1.293).
- Native auto memory: "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded".

## Codex (`https://learn.chatgpt.com/docs/hooks`, redirected from developers.openai.com/codex/hooks)

- "Installed plugins can also bundle lifecycle config through their plugin manifest or a default `hooks/hooks.json` file."
- "Installing or enabling a plugin doesn't automatically trust its hooks." (review in `/hooks` first)
- "Hooks are enabled by default." Events include SessionStart, PreCompact, PostCompact, PreToolUse, SessionEnd.
- SessionStart `hookSpecificOutput.additionalContext` "is added as extra developer context"; cap about 2,500 tokens per
  model-visible hook output by default, adjustable with `additionalContextLimit`.
- "Codex also sets `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility with existing plugin hooks."

## GitHub Copilot CLI (`https://docs.github.com/en/copilot/reference/hooks-configuration`)

- Events: agentStop, errorOccurred, notification, permissionRequest, postToolUse, postToolUseFailure, preCompact,
  preToolUse, sessionEnd, sessionStart, subagentStart, subagentStop, userPromptSubmitted, userPromptTransformed.
- "Only `additionalContext` is consumed for `sessionStart`."
- Plugin hooks are "declared by each plugin in its own `hooks.json` (or under `hooks/hooks.json`)".
- "Cross-tool `.claude/settings.json` and `.claude/settings.local.json` files in the repository are also read"; PascalCase
  event names get Claude matching rules.

## Cursor (`https://cursor.com/docs/hooks`, `/docs/plugins`) — via recon, not re-fetched by the integrator

- Native `sessionStart` returns `additional_context`; the agent loop does not wait for it (fire-and-forget); not run in
  cloud agents. Plugins can bundle hooks, skills, agents, rules, commands and MCP. UNVERIFIED by the integrator.

## OpenCode — via recon, not re-fetched

- `@opencode-ai/plugin` latest 1.19.3 (the kit pins 1.18.25). `experimental.session.compacting`: `output.prompt` replaces
  the default compaction prompt and `output.context` is ignored when it is set. `tool.execute.before` and `permission.ask`
  exist (a test guard is possible). UNVERIFIED by the integrator.

## Gaps docs cannot close

- Whether Codex / Copilot actually run THIS plugin's hooks on v7 — no CLI on this machine; unprobed.
- Whether an older Claude Code (< 2.1.295) accepts `onFailure` — probed by the 7.3 build (see CHANGELOG 7.3.0).

## README practice — six popular Claude Code plugin READMEs (recon, 2026-10-22)

Read in full via the GitHub API: obra/superpowers (303k★), thedotmack/claude-mem (102k★), anthropics/claude-plugins-official
(44k★), wshobson/agents (42k★), davila7/claude-code-templates (33k★), EveryInc/compound-engineering-plugin (26k★).

- 5 of 6 show a table or list with one line per component or component type; 3 of 6 list individual skills by name with
  a one-line purpose; 2 of 6 group skills by category.
- In 5 of 6 the inventory comes after Install; multi-host install sections dominate length in 3 of 6.
- 0 of 6 use Mermaid; 1 of 6 uses an ASCII tree (the Anthropic directory, for authors); 0 of 6 embed video; 2 of 6 have one
  inline GIF.
- Word counts 493–2,894, median about 1,700–2,000.
- GitHub renders fenced `mermaid` blocks in Markdown files and `<details>` collapsible sections
  (docs.github.com … creating-diagrams; … organizing-information-with-collapsed-sections).
