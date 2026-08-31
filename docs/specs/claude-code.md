# Claude Code — the baseline host (Tier 1)

Last verified: 2026-08-31, against the kit's own CI (`.github/workflows/checks.yml`) and a live
session. Claude Code is the canonical host: the plugin is authored in its format, and every
mechanism below is exercised by CI on each push — the whole file is `verified`.

## Mechanisms the kit actually uses

| Mechanism | Where | Contract |
|---|---|---|
| `SessionStart` hook | `hooks/session-start.py` | stdin JSON `{source}`, stdout `{hookSpecificOutput:{hookEventName,additionalContext}}`; profile per source (startup/clear/fork = full · compact = identity+memory · resume = nudges+stats) |
| `PreToolUse` hook | `hooks/protect-tests.py` | matcher `Edit\|Write`; emits `permissionDecision: ask/allow` — asks before editing an existing test not created this session |
| `PreCompact` hook | `hooks/pre-compact.sh` | emits `{decision:"block", reason}` unless MEMORY.md is fresh (<2 min) and inside all three caps |
| `SessionEnd` hook | `hooks/session-end.sh` | timestamp log only |
| Skill routing | `skills/*/SKILL.md` frontmatter | descriptions always in context; bodies load on invoke; namespaced `/memory-kit:<name>` |
| Subagents | `agents/*.md` | spawned via the Task tool by skills that orchestrate |
| `${CLAUDE_PLUGIN_ROOT}` | hooks.json, skill bodies | expands to the plugin cache dir; the hooks also carry cwd/`__file__` fallbacks, so they run without it |

## What a plugin cannot ship (why the delivery looks the way it does)

A Claude Code plugin cannot ship `CLAUDE.md`, `.claude/rules/`, or any `settings.json` key
other than `agent`/`subagentStatusLine`. The working agreement therefore travels as
`context/identity.md`, injected by the SessionStart hook — this constraint is the origin of
the kit's whole content-vs-delivery split, and the reason the T2 protocol file
(`templates/workspace/AGENTS-MEMORY-PROTOCOL.md`) could be distilled at all: the content was
already separated from the mechanism.

## Guarantees unique to this tier

- Memory is **injected**, not fetched — the agent wakes up already knowing (no instruction to
  forget to follow).
- Compaction **cannot** proceed over a stale cache (PreCompact block).
- Test-file edits are **intercepted**, not merely discouraged.

Every other host degrades some or all of these — see that host's spec.
