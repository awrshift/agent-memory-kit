---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# The window cycle — one main session and several windows

**Applies when:** you run more than one interactive session on one repository at a time, and one of them integrates.
**Take as is:** one session integrates; it starts from files, never from a window's memory; files carry the work.
**Adapt:** how many windows, how a task is cut into steps, the brief's lines, the slots, the close steps — one
project's.

`parallel-development.md` says when parallel work pays and that one session integrates. This file is how one project
runs it day to day: one MAIN session (the integrator: the user dialogue, decisions, merges, shared docs, memory) and
several WINDOWS (interactive sessions that build and report). Copy what fits; the counts are one project's.

## 1. The cycle and its close order

1. **Start from files.** Main starts cleared; the windows are open and clean. The past lives in files — the newest
   handoff's «Windows» section (§7), branches, commits, committed reports. Main never asks a window or the user what is
   still alive, and never starts from a window's memory. Held work is re-based first (`parallel-development.md`).
2. **Assign.** Each window gets ONE task by a brief FILE (§3). Main sends it itself; the message names the brief file,
   its commit and the first stop point. The user never pastes or relays a brief. A window's name for the session is its
   task; no role carries over from an earlier session.
3. **Work.** Windows build, report and wait at stop points; main verifies each report (`orchestrator-fact-check.md`)
   and gives the next task. **Main is never cleared or closed while a window works** — main holds the windows' context.
4. **Last tasks.** Past main's no-new-task line (`/memory-kit:close-session`), no window gets a task that cannot finish
   before main's close; a task that cannot finish is stopped at a clean state and recorded.
5. **Close, in this order:** every window finishes and reports → main accepts each result (`acceptance.md`) and saves
   what it needs into files → main finishes its own tasks → the handoff with its «Windows» section → the user clears
   the windows → the user clears main → step 1.

(one project's working practice; no count)

## 2. Files carry the work, messages point

The spec is a file in `projects/<name>/plans/`, the evidence beside it, the report a committed file in the spec's
report format. The message to main is at most five lines: the verdict, the report's path and commit, what main
must decide. A window is cleared at the close, so nothing lives only in a message — and
whatever main reads is paid from main's context; main reads a report's sections when it needs them, not whole.
Why: one project's window reports by message ran 2–8k characters; main's own whole-file reads were 40 % of its
context, window messages 5 % (measured in one project, 2026-11: main's session log).

A window reports after reading the code (what it found that changes the plan), at each stop point the brief names (then waits), before any
paid run, when blocked, and when finished. A premise main gives a window is checked by the window before it acts on it
(`orchestrator-fact-check.md`, «A statement carries its check») (one project's working practice; no count).

## 3. The coverage map, then the briefs

**Before the briefs, main commits a coverage map:** every stage and hypothesis of the source the work implements → its
owner — a window, the next session, or «not taken because …». An uncovered row is a decision, never an accident; in
one project a whole stage had no owner until the user asked (one project's working practice; no count).

**The brief** (`templates/workspace/WINDOW-BRIEF-TEMPLATE.md`) names: the task in one line · the resource slot (§5) ·
the spec path and commit · the worktree, branch and head · the stop points · each premise with the source it was read
from this session (a memory, handoff or report line is a pointer, not the source) · paid steps with a script's
estimate and cap, or «none» · each rule that drops or gates with its count on labelled rows (`measurement-lessons.md`)
· what «done» is and the report's shape. It also carries its rows of the coverage map with the source's measure
verbatim — a different measure is a registered deviation with its reason; in one project three measures drifted into
stand-ins unnoticed before this line existed (one project's working practice; no count).

## 4. Size and stop points

- **One deliverable per task, cut by work, not by a context number.** A task of more than one large step stops after
  each step and commits its state, so a cleared window restarts from files; the window's second task is named in the
  first brief. No window is asked to count, estimate or report its context (Anthropic's prompting guidance: avoid
  surfacing explicit context-budget counts to the model); the user sees the counter and says when a window closes.
  Why not a number: in one project three of four parallel sessions reported an estimate instead of the counter, one
  off by 90k, and a first step of four took 287k against ~200k estimated (one project's working practice, 2026-11).
- **Size the team to the task, not to the slots.** Pieces that share one context stay in one window; parallel windows
  only for separable work; an idle slot is fine. Fact sweeps and review seats go to helpers from the start
  (`helper-roster.md`). The critical path — the measurement a decision waits on — gets the first slot and the first
  spec. Anthropic's multi-agent research write-up says the same for its own system (fetched 2026-11-05)
  (one project's working practice; no count).

## 5. Fixed resource slots

When windows run services (a server port, a database, a cache index), each window owns a FIXED slot, named in the
brief's first line; main has its own. Before a boot the window checks its slot is empty; a non-empty slot is cleared
only by its own window, after the check shows nothing is running on it; another slot is never touched. Boot scripts
refuse a non-empty slot, and a helper that boots a service gets the window's slot in its brief. Why: on one day all
16 cache indexes of one project held leftover keys of old runs, and a helper once booted on another window's slot
(measured in one project, 2026-11: 16 of 16 indexes not empty).

## 6. Takeover — a window becomes the temporary main

When main must stop mid-session, the window its handoff names becomes main and the only writer (git, docs, the user
dialogue, main's slot); the old main stays alive but idle as a fallback.

1. Read the memory file and the newest handoff FROM DISK first — a cleared window can carry the session-start injection
   of an older day (seen once: the copy was a day old).
2. Ask in this order: repository files → a grep of the old main's transcript (matching lines only) → one batched
   message to the old main. Whatever is learned goes into a file in the same change.
3. Read the handoff's reading set from source before the first summary to the user — in one test the first summary was
   built from the decisions log and carried a stale number the plan had already corrected.
4. Log every gap; at the first close say whether the handoff alone was enough.

Tested twice on one day in one project (one project's working practice; no count).

## 7. The handoff's «Windows» section

Written by main at the close, per window: the task · branch and last commit · what is verified and how · what is not ·
the next step · resources kept (scratch databases, running services). The next main starts from this section
(one project's working practice; no count).
