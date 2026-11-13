---
created: 2026-11-11
last-reviewed: 2026-11-13
---

# The window cycle — one main session and three windows

**Applies when:** you run more than one interactive session on one repository at a time, and one of them integrates.
**Take as is:** one session integrates; it starts from files, never from a window's memory; files carry the work; one
task per window life.
**Adapt:** how many windows, how a task is cut into steps, the brief's lines, the slots, the close steps — one
project's.

`parallel-development.md` says when parallel work pays and that one session integrates. This file is how one project
runs it day to day: one MAIN session (the integrator: the user dialogue, decisions, merges, shared docs, memory) and
three WINDOWS (interactive sessions on the same repository that build, measure and report). The step-by-step for a
newcomer is in the root README, «Working as a team». Copy what fits; the counts are one project's.

## 1. The cycle and its close order

1. **Start from files.** Main starts cleared; three windows are open and clean, each started with a name
   (`claude --name w1`). Main finds them itself (`ListAgents`) and never asks the user to open or name them. The past
   lives in files — the newest handoff's «Windows» section (§7), branches, commits, committed reports. Main never asks
   a window or the user what is still alive. Held work is re-based first (`parallel-development.md`).
2. **Assign.** Each window gets ONE task by a brief FILE (§3). Main sends it itself by `SendMessage` to the window's
   listed name with `notify_when_idle: true`, so main hears when the window stops; the message names the brief file,
   its commit and the first stop point. The user never pastes or relays a brief. A window's name for the session is
   its task; no role carries over from an earlier session.
3. **Work.** Windows build, report and wait at stop points; main checks each report (`orchestrator-fact-check.md`;
   the gate receipt, `acceptance.md` §5), reads one real artifact itself, and gives the next step. Main does not poll
   or send «are you done?» — the idle notice says when.
4. **One task, one life.** When a window reports «finished», main's reply asks for its retro file (§8); the window is
   cleared (`/clear`) only after that file's commit is reported. The next task goes to a cleared window that starts
   from files.
5. **Last tasks.** A round's tasks are those of its plan and their continuations; main opens no second round in the
   same session. A task that cannot finish is stopped at a clean state and recorded (§7).
6. **Close, in this order:** every window finishes and reports → main accepts each result (`acceptance.md`) and saves
   what it needs into files → main finishes its own tasks → the handoff with its «Windows» section → the user clears
   the windows → the user clears main → step 1. When the user wants main closed while windows still work, main first
   tells each window it is leaving and the handoff names each window's step and the stop message main waits for; the
   next main tells each window it is back and asks it to repeat any stop message sent meanwhile.

**Visible windows, not background sessions.** One project tried a background session as the third slot and went back
to three interactive windows: the user wants to see the work as it happens, and a visible window's permission prompts
and stops reach a person (one project's working practice; no count).

(one project's working practice; no count)

## 2. Files carry the work, messages point

The spec is a file in `projects/<name>/plans/`, the evidence beside it, the report a committed file in the spec's
report format. The message to main is at most five lines: the verdict, the report's path and commit, what main
must decide. A window is cleared after its task, so nothing lives only in a message — and whatever main reads is paid
from main's context; main reads a report's sections when it needs them, not whole.
Why: one project's window reports by message ran 2–8k characters; main's own whole-file reads were 40 % of its
context, window messages 5 % (measured in one project, 2026-11: main's session log).

A window reports after reading the code (what it found that changes the plan), at each stop point the brief names (then
waits), before any paid run, when blocked, and when finished.

**Premises come in two kinds, and the brief keeps them apart:** read by main this session (with the file:line or
command) · taken from a report, a handoff or memory without a re-read. The window checks the second kind before it acts
on it; a wrong premise goes back in its next message with the evidence (`orchestrator-fact-check.md`, «A statement
carries its check») (one project's working practice; no count).

**The window never sends the user to itself.** Every decision is taken in one place, between the user and main. A
refused command or a permission prompt the window cannot pass goes to main with its exact text; main says what it is —
a deny rule nobody should approve (main names the allowed form) or a request (main asks the user in main's own session)
— and returns the answer. A window never asks the user to type a command (one project's working practice; no count).

## 3. The coverage map, then the briefs

**Before the briefs, main commits a coverage map:** every stage and hypothesis of the source the work implements → its
owner — a window, the next session, or «not taken because …». An uncovered row is a decision, never an accident; in
one project a whole stage had no owner until the user asked (one project's working practice; no count).

**The brief** (`templates/workspace/WINDOW-BRIEF-TEMPLATE.md`) carries these lines:

| Line | What it holds |
|---|---|
| Task | One line; the slot; who it reports to (main's listed name) |
| Spec | The contract's path and commit; worktree, branch and head |
| Binding rules | A pointer to the project's window rules (roles, no push, no shared docs) |
| Stop points | Each decision point where the window waits — at most three large steps |
| Premises | Read by main (with source) · from a report, not re-read (the window checks these first) |
| Paid | `none`, or «N units, ~cost from <script output>, cap» + the launcher (`spec-depth.md` §4) |
| Env | Vendor keys and credits as of the brief: which key is primary, which vendor is out |
| Rules on counts | Each rule that drops or gates, with its positive signal and its count on labelled rows (`measurement-lessons.md`) |
| At the limit | «Your context is not your concern — work at full depth, commit after every step» |
| Gates | The gate set; nothing heavy (a build, a replay, another test suite) runs while the gate runner runs — timer tests fail under load |
| Retro | The retro file's path (§8) |
| Done | The gate; the report's committed path; the ≤ 5-line message; the window's next task, for its next life |

The brief also carries its rows of the coverage map with the source's measure verbatim — a different measure is a
registered deviation with its reason; in one project three measures drifted into stand-ins unnoticed before this line
existed (one project's working practice; no count).

## 4. Size and stop points

- **One deliverable per life, cut by work, not by a context number.** A task of more than one large step — never more
  than three — stops after each and commits its state, so a cleared window restarts from files; the window's second
  task is named in the first brief. No window is asked to count, estimate or report its context (Anthropic's prompting
  guidance: avoid surfacing explicit context-budget counts to the model); the user sees the counter.
  Why not a number: in one project three of four parallel sessions reported an estimate instead of the counter, one
  off by 90k, and a first step of four took 287k against ~200k estimated (one project's working practice, 2026-11).
- **A fix round is a new life.** When a build is accepted for review or its review is in, the window writes its state
  to a file and is cleared; a clean window runs the fix round from the spec, the findings and the code. A build and its
  fix round are two tasks, never one — one window that ran tables, build and fix round in one life was stopped
  mid-round at its size (one project's working practice; no count).
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

## 8. The retro — every window life ends with one

Before it is cleared, each window writes a short committed file (≤ 25 lines) at the path its brief names, answering:
what was missing from the brief · where it waited for main and why · which decision of main it disagrees with · where
it erred and what would have caught it earlier · which premise was wrong and how it found out · what it built that
nothing reads · which of its numbers it would not defend. Once a day at a close, main counts the facts by script from
the session logs (plan vs done, corrections and who caught them, rework, wait time, spend vs estimate), answers its
own questions, and takes at most three changes, each at the strongest layer (a script or check, then a brief-template
line, then a rule). The next session opens by checking whether they fired. Causes are named in the system — the brief,
a rule, a check — never «be more careful» (`/memory-kit:session-review` carries the facts-by-script half)
(one project's working practice; no count).
