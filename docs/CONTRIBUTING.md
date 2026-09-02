# Contributing to Memory Kit

Thank you for your interest in contributing. This project is a plugin that gives an AI agent persistent memory as plain markdown in the user's own folder — authored in the Claude Code plugin format, installable on Cursor, Codex, Copilot CLI and OpenCode from the same manifests.

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
  `claude plugin validate --strict ./plugins/memory-kit` and `python3 tools/check-repo.py`, then
  run the changed hook against a scratch repo for EVERY SessionStart `source` (startup · resume ·
  compact · fork · clear). A broken profile fails silently — that class of bug lived in the kit
  for a year. CI (`.github/workflows/checks.yml`) repeats the hook probes and loads the OpenCode
  shim, but does not run `claude plugin validate` — that one is on you.
- A claim about a host other than Claude Code needs a probe, not a doc quote — record it in
  `docs/specs/<host>.md` with the label convention from `docs/specs/README.md`.
- If you change behavior, update `docs/CHANGELOG.md` (Added / Changed / Removed / Migration) and
  say so in the PR description. A layer change also touches `docs/ARCHITECTURE.md`.

## Ground rules

- **Zero dependencies.** Hooks and scripts use Python stdlib and bash only; the OpenCode shim uses Node built-ins only. No `pip install`, no `npm install`, no external services.
- **Pure Markdown for content.** Keep the wiki and memory plain `.md` so any editor and any agent works. No tool-specific syntax the plain file would not survive.
- **Don't invent new layers.** The kit ships exactly: `MEMORY.md`, `context/handoffs/`, `.claude/rules/`, plugin skills, `knowledge/concepts/`, and optionally `projects/` + `experiments/` in the user's repo. Proposals to add `playbooks/`, `wisdom/`, `lessons/`, `<role>-guidance/` need a high bar: we killed each at least once because real users never filled them, and the `daily/` chronicle went the same way — opt-in in v5, retired in v6.
- **Be kind in issues and PRs.** Assume good intent.

## What lives where (cheat sheet)

| If your contribution is... | It lives in... |
|---|---|
| New skill | `plugins/memory-kit/skills/<name>/SKILL.md` — namespaced `/memory-kit:<name>` automatically |
| New agent | `plugins/memory-kit/agents/<name>.md` |
| Script fix | `plugins/memory-kit/hooks/lib/` or `plugins/memory-kit/skills/<skill>/scripts/` — project paths from `CLAUDE_PROJECT_DIR`, never from `__file__` |
| A host other than Claude Code | `docs/specs/<host>.md` (probed, labeled) and, if it needs an adapter, a shim beside `.opencode/` — never a fork of the skill bodies |
| New hook | `plugins/memory-kit/hooks/<name>.{py,sh}` + register in `plugins/memory-kit/hooks/hooks.json` (never in a user's `settings.json`) |
| Depth that shouldn't sit in context | `plugins/memory-kit/reference/<name>.md` |
| Doc fix | `README.md`, `CLAUDE.md` (this repo's own), or `docs/*.md` |

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see `LICENSE` in the project root).
