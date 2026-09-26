---
name: setup
description: Adopt the Memory Kit in THIS repository — scaffold the memory layers, decide how the kit coexists with Claude Code's native auto memory, and install safe permission rails (`/memory-kit:setup rails` re-runs only the rails step on an adopted repo). Use when the user says "/memory-kit:setup", "/memory-kit:setup rails", "set up the memory kit", "adopt the kit here", "настрой кит", or when a session starts in a repo where the kit plugin is installed but no .claude/memory/MEMORY.md exists.
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
scaffolded upfront. An empty folder is not a layer; it is a promise nobody kept. `plans/` appears
with the first spec, written from `templates/workspace/project/SPEC-TEMPLATE.md`; an `executor`
told to build past a missing decision may add one `plans/<date>-<slug>-assumed.md` from
`ASSUMED-SPEC-TEMPLATE.md`, and nothing else in that folder is an agent's to create.

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

- **Kit owns memory (default).** Write `"autoMemoryEnabled": false` into `.claude/settings.json`
  (for CI or a headless run, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` does the same). You get dated
  entries, human-confirmed promotion, handoffs, and one file the user can read.
- **Both, side by side.** Leave auto memory on. It keeps writing its own index under
  `~/.claude/projects/<project>/memory/` (machine-local, outside the repo); the kit keeps the
  repo files and the ritual. Two writers, two truths — say so, and make the kit's `MEMORY.md`
  the one that counts for handoffs and promotion.

Do NOT point `autoMemoryDirectory` at the kit's `.claude/memory`: the setting only accepts an
absolute path or one starting with `~/` (so it cannot be committed portably), and Claude Code
would rewrite the kit's `MEMORY.md` in its own index format, overwriting the dated cache.

Whichever is chosen, say plainly which system now owns the file.

## Step 3 — permission rails (v2)

**`/memory-kit:setup rails`** (the argument `rails`, e.g. from the SessionStart «Rails:» line) runs
THIS step alone on an already adopted repo: skip Steps 0–2 and 4–6, build the proposal below, show
the diff of `.claude/settings.json`, merge on a yes and write `.claude/state/rails-v2`; on a no,
write `.claude/state/rails-declined`. Either file silences the nudge. A full setup writes the same
marker after this step. Headless: write nothing, report the proposal.

The plugin cannot ship permissions (Claude Code only honours `agent` and `subagentStatusLine`
from a plugin's `settings.json`) — the destructive git operations are already guarded by the
kit's git-guard hook (force push, `reset --hard`, `clean -f`, `branch -D`, `checkout .`,
`restore .`, `push --mirror`; opt-out `CMK_GIT_GUARD=off`). The rails cover the rest. Build the
proposal from what is actually in this repo:

1. **Env files that exist.** List the repo root: `.env`, `.env.local`, `.env.*.local`,
   `.env.development`, `.env.production`, `.env.test`, `*.pem`. For each one PRESENT, a
   `Read(./<name>)` and an `Edit(./<name>)` deny. Never `.env.example` / `.env.sample` — those
   are meant to be read.
2. **Ask before acting outside the repo:**

```json
{
  "permissions": {
    "deny": ["Read(./.env)", "Edit(./.env)"],
    "ask": [
      "Bash(gh pr create *)", "Bash(gh pr merge *)", "Bash(gh pr comment *)",
      "Bash(gh pr edit *)", "Bash(gh pr close *)", "Bash(gh pr review *)",
      "Bash(gh api -X *)", "Bash(gh api * -X *)", "Bash(gh api --method *)", "Bash(gh api * --method *)",
      "Bash(docker * down *)", "Bash(docker * down)", "Bash(docker rm *)", "Bash(docker * rm *)",
      "Bash(docker stop *)", "Bash(docker * stop *)", "Bash(docker kill *)", "Bash(docker * kill *)",
      "Bash(docker * prune*)"
    ]
  }
}
```

   (the `deny` pair shown is for a repo whose root holds `.env`; one pair per file found.)
3. **Drop the v1 prefix denies** `Bash(git push --force:*)` / `Bash(git push -f:*)` if present:
   a prefix cannot express «this flag anywhere», and the hook covers them. Say so in the diff.

State the rules out loud while you do it:

1. **A permission entry is a speed bump for the agent, never a guard on a script.** Anything that
   must not happen belongs inside the script or a hook. And **no broad allow** for git, gh,
   docker, curl or an interpreter (`Bash(git *)`, `Bash(node *)`, `Bash(python3 *)`, `Bash(*)`):
   in auto mode NARROW allow rules resolve BEFORE the classifier (Claude Code docs,
   auto-mode-config), so a broad one lets a destructive argument through unseen. The v5
   allowlist did exactly that — force pushes, hard resets, `node -e` — while reading as safety.
   A narrow allow names the EXACT script — `Bash(node scripts/foo.mjs *)`, never
   `Bash(node scripts/*)` / `Bash(python3 scripts/*)`: a path wildcard lets the agent write a new
   file into that folder and run it before the classifier sees it. The same for a runner whose
   subcommand executes arbitrary code: not `Bash(npx wp-env run *)`, only `Bash(npx wp-env run cli wp *)`.
   Point out broad allows already there; never remove the user's rules without a yes.
2. **An env file that a stand or script needs is loaded INTO a process, never read by the agent.**
   Preferred: a project launch script that loads it itself (`scripts/stand.sh`:
   `set -a; . ./.env; set +a; exec node …`) plus ONE narrow allow `Bash(bash scripts/stand.sh *)` —
   a narrow allow resolves before the classifier AND before Claude Code's built-in static check,
   which blocks an inline `set -a` whatever the settings say. Fallback only: one `autoMode.allow`
   sentence naming the file and the purpose.
3. **Env backups live outside the repo** (a `.env.bak` at the root is one more file to deny).
4. **Before adding `ask` rules, list the scripts that call `claude -p`** with gh or docker:
   headless mode turns an `ask` into a deny, so those scripts would start failing.

How to prove the rails afterwards: `${CLAUDE_PLUGIN_ROOT}/reference/harness-measurement.md` (M1).

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
