# Contributing to Claude Memory Kit

Thank you for your interest in contributing. This project is an OSS starter kit for Claude Code, focused on persistent memory and structured context management.

## Ways to contribute

- **Report a bug** — open an issue with steps to reproduce
- **Propose a feature** — open an issue describing the use case before writing code
- **Improve docs** — PRs for `README.md`, `docs/ARCHITECTURE.md`, the plugin's `context/identity.md`, or any `plugins/memory-kit/skills/<task>/SKILL.md` are welcome
- **Share a pattern** — open a discussion if you've found a memory or rules pattern that works well across projects

## The load-bearing invariant

**User only talks. Agent captures, proposes, writes.**

Any contribution that pushes users toward editing memory files manually — a script that surfaces patterns the user is then asked to review and edit, a UI that asks "review and approve this", a flow that says "open MEMORY.md and add" — will be rejected. The invariant is the value prop. Read `plugins/memory-kit/context/identity.md` and `docs/ARCHITECTURE.md` first.

## Pull requests

- Keep PRs focused. One feature or fix per PR.
- Match the existing style:
  - Pure Markdown for docs
  - Stdlib-only Python (no `pip install`)
  - English in everything tracked by git (skill examples can illustrate any-language conversation; the prose is English)
- Validate and exercise before pushing:
  `claude plugin validate ./plugins/memory-kit`, then run the changed hook against a scratch repo
  for EVERY SessionStart `source` (startup · resume · compact · fork · clear). A broken profile
  fails silently — that class of bug lived in the kit for a year.
- If you change behavior, update `docs/CHANGELOG.md` (Added / Changed / Removed / Migration) and
  say so in the PR description. A layer change also touches `docs/ARCHITECTURE.md`.

## Ground rules

- **Zero dependencies.** Scripts use Python stdlib only. No `pip install`. No external services beyond the `claude -p` subprocess.
- **Pure Markdown for content.** Keep the wiki and memory plain `.md` so any editor works.
- **Obsidian remains optional.** Don't add features that require Obsidian to be installed (wikilinks are the only Obsidian-style convention; they degrade cleanly to plain text).
- **Don't invent new layers.** The kit ships exactly: `MEMORY.md`, `context/handoffs/`, `.claude/rules/`, plugin skills, `knowledge/concepts/`, and optionally `projects/` + `experiments/` in the user's repo. Proposals to add `playbooks/`, `wisdom/`, `lessons/`, `<role>-guidance/` need a high bar: we killed each at least once because real users never filled them, and the `daily/` chronicle went the same way — opt-in in v5, retired in v6.
- **Be kind in issues and PRs.** Assume good intent.

## What lives where (cheat sheet)

| If your contribution is... | It lives in... |
|---|---|
| New skill | `plugins/memory-kit/skills/<name>/SKILL.md` — namespaced `/memory-kit:<name>` automatically |
| New agent | `plugins/memory-kit/agents/<name>.md` |
| Script fix | `plugins/memory-kit/scripts/<file>.py` — project paths from `CLAUDE_PROJECT_DIR`, never from `__file__` |
| New hook | `plugins/memory-kit/hooks/<name>.{py,sh}` + register in `plugins/memory-kit/hooks/hooks.json` (never in a user's `settings.json`) |
| Depth that shouldn't sit in context | `plugins/memory-kit/reference/<name>.md` |
| Doc fix | `README.md`, `CLAUDE.md` (this repo's own), or `docs/*.md` |

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see `LICENSE` in the project root).
