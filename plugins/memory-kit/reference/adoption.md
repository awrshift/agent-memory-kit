---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# Adoption — what to take as is, what to adapt, what to skip

> Read after an install or an upgrade of the kit: decide for each practice below — take it, adapt it or skip it —
> on THIS repository. `/memory-kit:setup adopt` walks this file with you. Most of these practices come from one
> project; the strength column says what each rests on, copied from the proof tag in its file.

**Applies when:** the kit was just installed or upgraded, or the user asks which of its practices this repository uses.

## The rule

- **Decide from the repository first** — the command in the row, the files, the git history, the session logs; ask
  the user only what the repository cannot show, once, in one message, each question with the default you would take.
- **Measured, and the condition matches** → adopt it as written.
- **In trial or one project's practice, and the condition matches** → adopt the invariant (the file's «Take as is»),
  set your own parameters (its «Adapt»), and write the date you will judge it.
- **The condition does not match** → skip it, and say so.
- **Never adopt in order to reorganise.**
- **A change to rules, agents or settings** (`.claude/rules/`, `.claude/agents/`, `.claude/settings.json`,
  `CLAUDE.md`) is proposed to the user and written after a yes.
- **Report** what you took, adapted and skipped, with the reason for each skip.

## The table

A command in the condition cell is a quick test — its output is a hint, read it before you decide. «See the file's
head» means the file carries its own «Take as is» and «Adapt» lines under its «Applies when».

| Condition (testable on your repository) | Open | Strength | Take · Adapt |
|---|---|---|---|
| You accept a helper's or another session's build after a review round | `reference/acceptance.md` · `templates/workspace/project/ACCEPTANCE-TEMPLATE.md` | measured (why) · in trial (the record, the receipt) | see the file's head |
| You delegate to helper agents more than a few times a session (hint: `ls .claude/agents/` shows that agent files exist, not how often you delegate) | `reference/helper-roster.md` · `templates/agents/` | in trial · one project's practice (the model split); the counts behind it measured | see the file's head |
| More than one interactive session on one repository at a time, one integrates (hint: `git worktree list` shows that worktrees exist, not how many sessions run at once) | `reference/window-cycle.md` · `templates/workspace/WINDOW-BRIEF-TEMPLATE.md` | one project's practice · in trial (the sizes) · measured (two reasons) | see the file's head |
| A spec is built by someone who did not write it, or its mechanism is a queue, a ledger or a lock | `reference/spec-depth.md` §3 | measured | Take: the read against the code at the base commit and against itself · Adapt: which specs beyond those three |
| A run costs money (hint: `grep -rli -e paid -e cost projects/*/plans/` shows plans that use the words, not that a run costs money) | `reference/spec-depth.md` §4 | one project's practice | Take: «N units, ~cost, cap» before the run, the script stops at the cap · Adapt: the money line — the user sets it |
| You write a fix spec for a defect of a kind seen before (a `review-findings.md` exists) | `reference/review-loop.md` §0 · `templates/workspace/project/SPEC-TEMPLATE.md` | measured (the gap) · in trial (the lines) | Take: the Family and Fix layer lines on every fix spec · Adapt: whether a script refuses a spec without them |
| You keep a findings registry (`ls projects/*/review-findings.md`) | `reference/review-loop.md` §2 | one project's practice | Take: a process slip is a row naming the rule that should have fired · Adapt: the registry's columns |
| Finished work waits unsent while its target moves (`git branch --no-merged <target>`) | `reference/parallel-development.md` «Held work drifts» | measured (the drift) · in trial (the rules) | Take: re-base held lines at session start · Adapt: the «Other tops» line, whether a script checks it |
| An item outruns its estimate, or work waits for someone else's review | `reference/parallel-development.md` «Stop-conditions» | one project's practice | Take: past twice its estimate → «continue / reshape / stop» to the user · Adapt: the waiting-work cap |
| You tell the user how the code, the data or a run is now, or act on a premise handed to you | `reference/orchestrator-fact-check.md` «A statement carries its check» | measured · one project's practice (the premise check) | Take: the statement travels with its command or file line · Adapt: nothing |
| The same judgment task recurs too often to read every item yourself | `reference/measurement-lessons.md` §1 | one project's practice | see the file's head (§1) |
| You count or judge a system's output to decide a change | `reference/measurement-lessons.md` §2 | measured | see the file's head (§2) |
| You review code that takes outside input, runs queued or retried work, or acts on model output | `reference/review-classes.md` | one project's practice | see the file's head |
| The user reads your messages without having watched the work, or answers with comments | `reference/reporting.md` | one project's practice · measured (one line) | see the file's head |
| Your always-loaded instructions grew one line per incident (hint: `git log --oneline -- CLAUDE.md .claude/rules/` shows that they changed, not that each change was one line per incident) | `reference/rules-subtraction.md` | measured (sizes, contradictions) · in trial (the effect) | see the file's head |
| More than one document tracks progress or the order of work | `reference/doc-governance.md` R1 | one project's practice | Take: derived state is not kept by hand; the order of work has one home · Adapt: which file or script is it |
| You delete, move or reorganise more than a handful of files | `reference/doc-governance.md` R3 | measured (one reorganisation) | Take: the change rewrites live references in the same change; its gate runs every consumer · Adapt: the script |
| Your project keeps check scripts that find their subject in the tree | `reference/project-extensions.md` «Telemetry» | measured | Take: fail on an empty subject; anchor by name or shape; break what a proof row proves · Adapt: which checks |
| You are about to add a guard on briefs, or take a regular expression into a hook | `reference/project-extensions.md` «Measured and not built» | measured | Take: time a hook's regex on a hostile line first · Adapt: repeat a study when your defects differ |
| You size a session start, run sessions in parallel, or decide what to give a helper | `reference/harness-measurement.md` «Harness notes» | measured (start sizes) · fetched 2026-11-11 (docs facts, one UNVERIFIED) · one project's practice (the helper lines) | Take: measure start sizes from usage; cut long work by steps, not by a context number · Adapt: the numbers; re-check after an update |
| A PR body, release note or message you hand over names paths or commits | `scripts/claim-refs-check.py` · `skills/document/SKILL.md` | one project's practice | Take: run it before the text leaves · Adapt: the `--repo` list |
| Your sessions run long enough to near an automatic compaction (`/context` late in a session) | `skills/close-session/SKILL.md` «Also check» | one project's practice | Take: the close begins while there is room to finish it, with no context count · Adapt: your project's own session-length rule |
| The kit keeps memory here (`ls .claude/memory/MEMORY.md`) | `skills/close-session/SKILL.md` step 1 | one project's practice | Take: grep the topic before adding a line; replace or merge, never stack · Adapt: nothing |
| You run a retro over past sessions | `skills/session-review/SKILL.md` §6 | one project's practice | Take: the facts come from the session logs by script, at most three changes · Adapt: the script, the cadence |

