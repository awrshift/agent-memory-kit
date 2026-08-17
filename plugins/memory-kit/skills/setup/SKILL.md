---
name: setup
description: Adopt the Memory Kit in THIS repository — scaffold the memory layers, decide how the kit coexists with Claude Code's native auto memory, and install safe permission rails. Use when the user says "/memory-kit:setup", "set up the memory kit", "adopt the kit here", "настрой кит", or when a session starts in a repo where the kit plugin is installed but no .claude/memory/MEMORY.md exists.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /memory-kit:setup — adopt the kit in an existing repository

The plugin ships behaviour; the repository owns the state. This skill creates that state —
**always asking before the first write**, and never touching files the repo already has.

## Step 0 — look before you write

Report in two lines what already exists: `.claude/memory/MEMORY.md`, `context/handoffs/`,
`knowledge/`, `.claude/settings.json`, `.gitignore`, and whether this is a git repo with code
(a real project) or an empty folder (a fresh memory workspace). Everything after this is a
proposal the user confirms once, not a sequence of prompts.

## Step 1 — the memory layers

Create only what is missing, copying from `${CLAUDE_PLUGIN_ROOT}/templates/`:

| Path | From | Purpose |
|---|---|---|
| `.claude/memory/MEMORY.md` | `templates/MEMORY-TEMPLATE.md` | the hot cache the hook injects every session |
| `context/handoffs/HANDOFF-TEMPLATE.md` | `templates/HANDOFF-TEMPLATE.md` | the per-session note format |
| `knowledge/index.md` | `templates/workspace/knowledge-index.md` | the catalog of deep memory |
| `knowledge/concepts/.gitkeep` | — | where promoted patterns land |
| `.claude/state/.gitkeep` | — | hook bookkeeping (gitignored) |

For a **memory workspace** (not a code repo) also offer `projects/` and `experiments/` from
`templates/workspace/` — for a real code repository do NOT, they are noise there.

## Step 2 — the auto-memory decision (ask, do not assume)

Claude Code has its own auto memory (`~/.claude/projects/<project>/memory/`, loaded every
session, written by Claude without asking). Running it alongside the kit means two writers and
two truths. Put the choice to the user in one question:

- **Kit owns memory (default).** Write `"autoMemoryEnabled": false` into `.claude/settings.json`.
  You get dated entries, human-confirmed promotion, handoffs, and one file the user can read.
- **Native owns capture, kit owns the ritual.** Set `"autoMemoryDirectory"` to this repo's
  `.claude/memory` and lower the caps to the native limits (200 lines / 25 KB) — the audit,
  promotion and handoffs still come from the kit.

Whichever is chosen, say plainly which system now owns the file.

## Step 3 — permission rails

The plugin cannot ship permissions (Claude Code only honours `agent` and `subagentStatusLine`
from a plugin's `settings.json`), so propose this merge into the project's
`.claude/settings.json` — and never widen an existing allowlist without saying so:

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./**/*.pem)"
    ],
    "ask": [
      "Bash(git reset --hard:*)",
      "Bash(git clean:*)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

State the rule out loud while you do it: **a permission entry is a speed bump for the agent,
never a guard on a script.** Anything that must not happen belongs inside the script itself.

Do NOT reproduce the v5 allowlist (`Bash(git *)`, `Bash(npm *)`, `Bash(node *)`,
`Bash(python3 *)`). It read as a safety feature while auto-approving force-pushes, hard resets
and arbitrary code execution through `node -e`.

## Step 4 — .gitignore

Append only the lines that are missing, each with its reason in one comment:

```gitignore
.claude/state/*
!.claude/state/.gitkeep
.claude/memory/MEMORY.md      # personal hot cache — commit deliberately if the team shares it
context/handoffs/*.md         # session notes; keep the template
!context/handoffs/HANDOFF-TEMPLATE.md
```

For a **team** repository, ask instead: shared memory (commit both) is often the point.

## Step 5 — the optional layers (offer, install nothing by default)

The plugin also carries a builder's toolkit. None of it costs context until invoked, so it is
already available — the only thing that needs a decision is the always-loaded rule:

- **Building with subagents?** Offer to copy `${CLAUDE_PLUGIN_ROOT}/templates/rules/orchestration.md`
  into `.claude/rules/`. Five invariants, always loaded, ~20 lines — that is the entire cost.
  The agents (`executor`, `recon`, `idea-validator`) and `/memory-kit:session-review` +
  `/memory-kit:second-opinion` work without it; the rule is what makes the discipline binding.
- **Shipping a product with a UI?** `/memory-kit:qa-sweep` needs a protocol first: copy
  `${CLAUDE_PLUGIN_ROOT}/reference/qa-PROTOCOL-TEMPLATE.md` → `docs/qa/README.md`, fill every
  `<placeholder>`, and merge `reference/qa-mcp.json.example` into the project `.mcp.json`.
  Do this only when the user asks for QA — never as part of a default setup.
- Depth for the rest lives in `${CLAUDE_PLUGIN_ROOT}/reference/` and is read on demand.

## Step 6 — verify, then hand back

1. `/context` → confirm the plugin's SessionStart injection is present.
2. Confirm the hot cache is actually in context. If it is not, the injection failed — say so;
   do not claim the kit is live.
3. Tell the user, in three lines: what was created, who owns memory now, and that
   `/memory-kit:close-session` is what they type at the end of the day. Offer `/memory-kit:tour`.

## What NOT to do

- Don't scaffold silently, and don't create `projects/`+`experiments/` in a code repository.
- Don't overwrite an existing `MEMORY.md`, `settings.json` or `.gitignore` — merge, and show
  the diff before writing.
- Don't invent layers. `MEMORY.md`, `context/handoffs/`, `knowledge/concepts/`,
  `.claude/rules/` — that is the whole system.
- Don't declare success from the file listing alone. The v5 kit spent a year claiming the hot
  cache was "always loaded" while it was never injected; the only proof is seeing it in context.
