---
name: setup
description: Adopt the Memory Kit in THIS repository — scaffold the memory layers, decide how the kit coexists with Claude Code's native auto memory, and install safe permission rails. Use when the user says "/memory-kit:setup", "set up the memory kit", "adopt the kit here", "настрой кит", or when a session starts in a repo where the kit plugin is installed but no .claude/memory/MEMORY.md exists.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /memory-kit:setup — adopt the kit in an existing repository

The plugin ships behaviour; the repository owns the state. This skill creates that state —
**always asking before the first write**, and never touching files the repo already has.

Running without a user who can answer (a headless or `-p` run)? Then "offer" means **skip and
report**: take the documented default where one exists, install nothing that the skill marks as
opt-in, and finish with a list of what was deliberately not installed and what question is still
open. Never invent a preference on the user's behalf and never present a skipped step as done.

Running under a host other than Claude Code (Codex and others load this skill too)?
`${CLAUDE_PLUGIN_ROOT}` will not expand there — resolve every plugin path in this skill
relative to this SKILL.md file's own location (`../../` is the plugin root), and skip the
Claude-Code-only steps (`settings.json` keys, `/context`) with a one-line note.

## Step 0 — look before you write

Report in two lines what already exists: `.claude/memory/MEMORY.md`, `context/handoffs/`,
`knowledge/`, `projects/`, an existing documentation home (`docs/`, `doc/`, `documentation/`),
`.claude/settings.json`, `.gitignore`, and whether this repo already holds work of its own —
code, or documents other than a bare README (a real project) — or is effectively empty (a fresh
memory workspace). Being a git repo decides nothing; content does. Everything after this is a proposal the user
confirms once, not a sequence of prompts.

## Step 1 — the shared memory layers

These four are shared across every project in the repo. Create only what is missing, copying
from `${CLAUDE_PLUGIN_ROOT}/templates/`:

| Path | From | Purpose |
|---|---|---|
| `.claude/memory/MEMORY.md` | `templates/MEMORY-TEMPLATE.md` | the hot cache the hook injects every session |
| `context/handoffs/HANDOFF-TEMPLATE.md` | `templates/HANDOFF-TEMPLATE.md` | the per-session note format |
| `knowledge/index.md` | `templates/workspace/knowledge-index.md` | the catalog of deep memory |
| `knowledge/concepts/.gitkeep` | — | where promoted patterns land |
| `.claude/state/.gitkeep` | — | hook bookkeeping (gitignored) |

## Step 1b — the project layer (`projects/<name>/`)

The four layers above hold MEMORY. The work's own documents — tasks, specs, research, decisions,
QA — belong to a PROJECT, and the kit is multi-project by design: one folder per client or
product, so that a decision ledger, a findings registry and a QA protocol each count and describe
exactly ONE thing. **This applies to a single-product code repository too** — it simply has one
project folder, named after the product. (Earlier versions told you to skip `projects/` in a code
repo. That left specs, backlogs and research with no home, and they scattered into the repo root.)

Ask for the name(s), then create per project — nothing more:

| Path | From | Purpose |
|---|---|---|
| `projects/<name>/README.md` | `templates/workspace/project/README-TEMPLATE.md` | what it is + **the map of where its documents live** |
| `projects/<name>/BACKLOG.md` | `templates/workspace/project/BACKLOG-TEMPLATE.md` | tasks and their real status |

The rest of the project layer — `plans/`, `research/`, `decisions-log.md`, `review-findings.md`,
`qa/`, `materials/` — is **created on first use by whoever produces the artifact**, never
scaffolded upfront. An empty folder is not a layer; it is a promise nobody kept.

**If the repository already has a documentation home**, do NOT move anything and do NOT propose a
migration. Fill the README's map table with the paths it already uses, written from the repo root
with a leading `/` so they can't be misread as project-relative. That table is the SSOT for "where
does a plan go" — the defaults are a default, not a law, and a repo's own layout outranks them.

The test for "already has one" is **committed content, not a folder**: a `docs/` (or `doc/`,
`documentation/`) holding at least one markdown file that git tracks and that a human wrote. An
empty directory, or one holding only scaffolding you cannot attribute to anyone, does not count —
use the defaults. When the call is genuinely close, ASK; it decides where every future plan gets
looked for, and it is cheap to ask once and expensive to split a repo's documents across two homes.

Brand-new empty workspace, first time with the kit? Also offer the `experiments/` sandbox from
`templates/workspace/`, and — **only when there is exactly one project** —
`templates/workspace/ONBOARDING-BACKLOG.md` as its backlog: five guided tasks for day one. With
two or more real projects on day one, skip it (a tutorial mixed into a client's backlog is noise,
and a third fake project to hold it is worse) and offer `/memory-kit:tour` instead.

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

For a **team** repository — more than one human committing, or a shared remote anyone on the
team can push to — ask instead: shared memory (commit both) is often the point. Solo or private:
the defaults above.

## Step 5 — the optional layers (offer, install nothing by default)

The plugin also carries a builder's toolkit. None of it costs context until invoked, so it is
already available — the only thing that needs a decision is the always-loaded rule:

- **Building with subagents?** Offer to copy `${CLAUDE_PLUGIN_ROOT}/templates/rules/orchestration.md`
  into `.claude/rules/`. Five invariants, always loaded, ~20 lines — that is the entire cost.
  The agents (`executor`, `recon`, `idea-validator`) and `/memory-kit:session-review` +
  `/memory-kit:second-opinion` work without it; the rule is what makes the discipline binding.
- **Other agents also work in this repo (Codex, Cursor, Copilot — anything that auto-loads
  `AGENTS.md`)?** Offer to append the block from
  `${CLAUDE_PLUGIN_ROOT}/templates/workspace/AGENTS-MEMORY-PROTOCOL.md` to the repo's
  `AGENTS.md` — create the file if missing; if it exists, append and show the diff first,
  never overwrite what is already there. The block is fenced by
  `<!-- memory-kit protocol … -->` markers: on a later kit upgrade REPLACE the marked block,
  don't stack a second copy. This hands non-hook hosts the same discipline as an always-loaded
  instruction; Claude Code itself doesn't need it (the hooks enforce it). Details on what each
  host can and cannot honour: `docs/specs/` in the kit repository.
- **Shipping a product with a UI?** `/memory-kit:qa-sweep` needs a protocol first: copy
  `${CLAUDE_PLUGIN_ROOT}/reference/qa-PROTOCOL-TEMPLATE.md` → `projects/<name>/qa/README.md`,
  fill every `<placeholder>`, and merge `reference/qa-mcp.json.example` into the project
  `.mcp.json`. Do this only when the user asks for QA — never as part of a default setup.
- **Adding your own skills, hooks or agents to this repo?** `${CLAUDE_PLUGIN_ROOT}/reference/project-extensions.md`
  is the decision table for which shape a repeated workflow takes and what it costs when idle.
- Depth for the rest lives in `${CLAUDE_PLUGIN_ROOT}/reference/` and is read on demand.

## Step 6 — verify, then hand back

The files you just created were NOT in context when this session started, so nothing you can see
right now proves the injection works. Prove it the only honest way — run the hook yourself and
read what it would inject next time:

```bash
HOOK="${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py"
# the variable expands in this skill's text, not in your shell — fall back to finding the file
[ -f "$HOOK" ] || HOOK=$(find ~/.claude/plugins -path '*memory-kit*' -name session-start.py | head -1)
CLAUDE_PLUGIN_ROOT="$(dirname "$(dirname "$HOOK")")" python3 "$HOOK" <<< '{"source":"startup"}'
```

1. The output must contain the working agreement AND a section holding your new `MEMORY.md`
   body. If it still shows the "not set up in this repository" pointer, the scaffold landed in
   the wrong place — say so; do not claim the kit is live.
2. Then, in an interactive session only, `/context` as a second check — it shows THIS session's
   opening injection, so a missing hot cache there is expected today and confirmed on the next
   start. In a headless run there is no `/context`; the hook output above is the whole proof.
3. Tell the user, in three lines: what was created, who owns memory now, and that
   `/memory-kit:close-session` is what they type at the end of the day. Offer `/memory-kit:tour`.

## What NOT to do

- Don't scaffold silently, and don't create the project subfolders (`plans/`, `research/`,
  `qa/`, …) upfront — they appear when something is actually written into them.
- Don't move a repository's existing `docs/` into `projects/`. Map it, never migrate it.
- Don't overwrite an existing `MEMORY.md`, `settings.json` or `.gitignore` — merge, and show
  the diff before writing.
- Don't invent layers. Memory is `MEMORY.md`, `context/handoffs/`, `knowledge/concepts/`,
  `.claude/rules/`; the work's documents live in `projects/<name>/`. That is the whole system.
- Don't declare success from the file listing alone. The v5 kit spent a year claiming the hot
  cache was "always loaded" while it was never injected; the only proof is seeing it in context.
