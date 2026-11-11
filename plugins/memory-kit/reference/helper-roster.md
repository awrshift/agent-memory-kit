---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# Helper roster — a named role and an explicit model on every helper call

**Applies when:** you delegate to helper agents (subagents) more than a few times a session.

The always-loaded invariants (`templates/rules/orchestration.md`) say a helper executes a decided spec, its report is
input, and a long-lived helper is replaced by a fresh one. `project-extensions.md` gives the skeleton of one agent file.
This file is the difference: a fixed set of roles, how each call picks one, and what a role file must carry when the
helper starts without the project's rules.

## 1. Every call names a role and a model

- **A role, from a fixed roster.** Every recurring job has one agent file with its own prompt, tool list and output
  shape. A call to the built-in general-purpose agent says in its brief why no role fits — those calls are the roster's
  gap signal: a job seen twice there gets a role (in trial in one project since 2026-11-11; count due 2026-11-18).
  Why: over one week of 266 helper calls in one project, 63 went to the general-purpose agent with a prompt composed on
  the spot (measured in one project, 2026-11: 63 of 266 calls without a role).
- **An explicit model on every call** — an omitted model inherits the main loop's. The split: **the stronger model
  where the helper judges** (a build, a code review, a spec read, labelling by a rubric, a draft the user will read),
  **the cheaper one where it only collects or counts** (fact sweeps, greps, tallies). A usage limit that forces the
  cheaper model is said in the report (one project's working practice; no count).

## 2. The roles

The kit lists four agents of its own (`executor`, `recon`, `idea-validator`, `qa`). Five more ship as templates to
copy into your `.claude/agents/` (`/memory-kit:setup` offers it); adapt the paths and the gates to your project.

- `code-reviewer` (stronger model) — a built diff or a fix diff against its spec, by someone who did not write it →
  the review record `acceptance.md` §1–2 reads.
- `prebuild-reader` (stronger) — a spec against the code at its base commit, and against itself, before the build →
  a blocking / note list (`spec-depth.md` §3).
- `tool-builder` (stronger) — scripts, harnesses, checks with a self-test; not product code → the script, its saved
  output, its limits.
- `web-recon` (cheaper) — an external fresh-check: a vendor's API, price, version, a practice → fact · quote · URL ·
  date.
- `labeler` (stronger) — rows labelled by a written rubric, blind to the hypothesis → one table + counts by command.

The templates live in `templates/agents/` (`code-reviewer.md`, `prebuild-reader.md`, `tool-builder.md`,
`web-recon.md`, `labeler.md`). The kit's `recon` keeps facts from your own repositories; `web-recon` splits off the
web half so each prompt stays narrow (in trial in one project since 2026-11-11; count due 2026-11-18).

## 3. A helper may start without the project's rules — so its file carries them

An agent file with `omitClaudeMd: true` starts without the user, project and local `CLAUDE.md` files and without the
always-loaded rules; path-scoped rules and a subfolder's `CLAUDE.md` still load when it works with files there (Claude
Code docs, sub-agents page, fetched 2026-11-11). Hooks are the harness's, not the prompt's — in one project the git
guard still blocked inside such a helper; other guards were not probed, so probe each one you rely on.

The saving is large: a do-nothing helper started at 42.8k tokens with every tool and rule, 18.3k without the rule
files, and 4.9k with a six-tool list on top; one project's seven roles started at 5.3k–7.8k tokens against
30.9k–58.8k before (measured in one project, 2026-11: first-call usage of each role).

The price: what the helper must know is no longer loaded for it. For every rule a role must obey, decide where it lands
— the role's body · a file the body tells it to read · the caller's brief · a hook · «not for helpers» (it stays with
the integrator: talking to the user, memory, the session close). A rule with no landing place is a rule the helper
does not know. What always goes in the brief: paths, worktree and head, the gates, the caps, the output path, what
not to touch (in trial in one project since 2026-11-11; count due at the next three builds measured against the old
executor runs).

## 4. Tools, least privilege — and what a role cannot do

- An explicit `tools` list is a limit the harness enforces, not a request in a prompt. Leave out the agent-spawning
  tool: **a helper cannot call helpers**, so a job that needs a fan-out is split by the integrator, not inside the
  helper. Leave out the skill tool unless the role runs a skill.
- **A brief names what the role cannot do** when the job brushes against it — no helpers to spawn, no edit for a
  read-only role, no web for `recon`, no paid call without a cap the brief grants — so the helper reports the gap
  instead of working around it (one project's working practice; no count).
- Same-named agents (a plugin's and a project's) and how a project switches one off: `harness-measurement.md`.

## 5. How a role file is written

Anthropic's agent-writing guide (its plugin-development skill, read 2026-11-11): `description` is the field the router
reads — «Use this agent when …», two to four typical triggers, and when NOT to use it; a second-person body with Core
Responsibilities · Process · Quality Standards · Output Format · Edge Cases; best 500–3,000 characters, under 10,000.
One project adds a «Never» block for the hard limits and an `effort` line, and fixes the reviewer's output headings to
what its acceptance check parses (one project's working practice; no count).

## 6. Proving a roster change

A roster change is a harness change (`harness-measurement.md`): the start context per role from the first call's usage,
before and after · each guard you rely on probed inside a lean helper · the new reviewer, blind, on past diffs whose
blocking findings are known. One project's reviewer replay found the known blocking findings on 3 of 3 diffs, with one
extra valid finding and none false (measured in one project, 2026-11: 3 of 3 diffs). Token savings per build and
quality per build are counted on the next real builds, not on the probe.
