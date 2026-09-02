# Claude Cowork (desktop) — skills only, no hooks

Last verified: 2026-09-02, `documented-only` — from Anthropic's plugin reference and open
issues in `anthropics/claude-code`; not probed by us (a probe needs a Cowork seat and a
synced plugin, see the checklist).

Why this host matters: Cowork is the Claude app for people who do not live in a terminal —
exactly the solo operator the kit is written for. The community marketplace
(`anthropics/claude-plugins-community`) serves **both** Claude Cowork and Claude Code, so a
listing there puts the kit in front of Cowork users, and what they get must be stated honestly.

## What is known

| Claim | Label | Evidence |
|---|---|---|
| Cowork installs plugins enabled for the claude.ai account into `~/.claude/plugins/synced/` and loads each as `<name>@synced` | `documented-only` | `code.claude.com/docs/en/plugins-reference`, "synced plugins" |
| Skills from a marketplace plugin work in Cowork sessions | `documented-only` | reporters in issues #27398 and #51281 state skills from the same plugin work while hooks do not |
| Plugin `hooks/hooks.json` does NOT fire in Cowork (SessionStart, PreToolUse, PreCompact alike); the session is spawned with `--setting-sources user`, which excludes plugin-scoped hooks | `documented-only` | `anthropics/claude-code` issues #27398 (2026-02), #47993 (2026-04, feature request for SessionStart), #51281 (2026-04); all open as of this date |
| `CLAUDE.md` instructions are read but "routinely skipped in favor of the user's first message" | `documented-only` | issue #47993, reporter's account |

## What that means for the kit

- **No injection, no compaction block, no test guard.** Cowork is Tier 2 at best: the 8 skills
  are available (`/memory-kit:setup`, `/memory-kit:close-session` work as skills), and the
  memory files are plain text the agent can be told to read.
- The `AGENTS.md` protocol block does not apply (Cowork reads `CLAUDE.md`, not `AGENTS.md`).
  The honest substitute is the same protocol block appended to the folder's `CLAUDE.md` —
  `/memory-kit:setup` should offer that when it detects no hook ran (`manual-check-needed`:
  setup does not yet detect the host).
- "Wakes up already knowing" does not exist here until Anthropic ships plugin hooks in Cowork
  (#47993). Re-verify on every Cowork release note that mentions hooks or plugins.

## Manual checklist (to turn `documented-only` into `verified`)

1. Enable the kit for the claude.ai account, open a Cowork session in a folder that has
   `.claude/memory/MEMORY.md` with a canary line.
2. Ask "what is in your context about memory?" before any file read — the canary present means
   injection works; absent means hooks did not fire.
3. `/memory-kit:setup` and `/memory-kit:close-session` as skills: do they run, do they write.
4. Record the Cowork version and date here.
