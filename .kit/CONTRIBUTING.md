# Contributing to Claude Memory Kit

Thank you for your interest in contributing. This project is an OSS starter kit for Claude Code, focused on persistent memory and structured context management.

## Ways to contribute

- **Report a bug** — open an issue with steps to reproduce
- **Propose a feature** — open an issue describing the use case before writing code
- **Improve docs** — PRs for `README.md`, `CLAUDE.md`, `.kit/ARCHITECTURE.md`, or any `.claude/skills/<task>/SKILL.md` are welcome
- **Share a pattern** — open a discussion if you've found a memory or rules pattern that works well across projects

## The load-bearing invariant

**User only talks. Agent captures, proposes, writes.**

Any contribution that pushes users toward editing memory files manually — a script that surfaces patterns the user is then asked to review and edit, a UI that asks "review and approve this", a flow that says "open MEMORY.md and add" — will be rejected. The invariant is the value prop. Read `CLAUDE.md` and `.kit/ARCHITECTURE.md` first.

## Pull requests

- Keep PRs focused. One feature or fix per PR.
- Match the existing style:
  - Pure Markdown for docs
  - Stdlib-only Python (no `pip install`)
  - English in everything tracked by git (skill examples can illustrate any-language conversation; the prose is English)
- Test scripts locally before pushing: `python3 .kit/advanced/scripts/lint.py` on your changes (the Python tooling lives in `.kit/advanced/`)
- If you change behavior, update `.kit/CHANGELOG.md` (Added / Changed / Removed / Migration sections) and mention the change in the PR description

## Ground rules

- **Zero dependencies.** Scripts use Python stdlib only. No `pip install`. No external services beyond the `claude -p` subprocess.
- **Pure Markdown for content.** Keep the wiki and memory plain `.md` so any editor works.
- **Obsidian remains optional.** Don't add features that require Obsidian to be installed (wikilinks are the only Obsidian-style convention; they degrade cleanly to plain text).
- **Don't invent new layers.** The kit ships exactly: `daily/`, `MEMORY.md`, `.claude/rules/`, `.claude/skills/<task>/`, `knowledge/concepts/`, `projects/`. Proposals to add `experiences/`, `playbooks/`, `wisdom/`, `lessons/`, `<role>-guidance/` etc. need a high bar. We've killed each of those at least once because real users didn't fill them.
- **Be kind in issues and PRs.** Assume good intent.

## What lives where (cheat sheet)

| If your contribution is... | It lives in... |
|---|---|
| New default slash operator | `.claude/commands/<name>.md` (thin wrapper) + `.claude/skills/<name>/SKILL.md` (logic) |
| New opt-in command / fix to a script | `.kit/advanced/commands/<name>.md` + `.kit/advanced/scripts/<file>.py` |
| New hook | `.claude/hooks/<name>.{sh,py}` + register in `.claude/settings.json` |
| Doc fix | `README.md`, `CLAUDE.md`, or `.kit/*.md` |

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see `LICENSE` in the project root).
