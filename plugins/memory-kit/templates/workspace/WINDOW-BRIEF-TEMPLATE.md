<!-- from one project's practice, in trial since 2026-11; count due 2026-11-25; see reference/window-cycle.md -->
<!-- Applies when: you run more than one session at a time — one main session and windows that build or measure. -->

# <window name> — brief: <task, one line>

The main session fills the block, saves it as a file the window reads (beside the task's spec), and sends the window
one message that points at that file. The procedure behind every line: the plugin's `reference/window-cycle.md`.

```
Window <name> — task: <one line>. Slot <name> (only if the project shares resources). Reports to <main's listed name>.
Spec (the contract): <path> (commit <hash>). Worktree <path>, branch <name> at <head hash>.
Binding rules: <the project's window rules — no push, no PR, no shared docs, no user decision>.
Stop points: <each decision point where the window stops and waits for main; at most three large steps>.
Premises: read by main this session — <each fact with its file:line or command> · from a report, handoff or memory, NOT
  re-read by main — <each named as such; check these first>.
Paid: none | <N units, ~cost from <script output file>, cap>. Launcher: <the committed script that loads the
  environment inside itself>; its free dry run and a free probe of every vendor key are shown before main's yes.
Env: <vendor keys and credits as of the brief — which key is primary, which vendor is out>.
Rules that drop or gate: <each with its positive signal and its count on labelled rows>.
At the limit: your context is not your concern — work at full depth and commit after every step; a cleared window
  continues from the files.
Gates: <the gate set>. Nothing else heavy (a build, a replay, another test suite) runs while the gate runner runs.
Retro: <path of this life's retro file>.
Done = <the gate>; report = a committed file at <path>; message to main ≤ 5 lines:
  verdict · report path · commit · what main must decide. Your next task, in a new life: <one line>.
```

The rules behind the lines live in `reference/window-cycle.md`: one task per window, the second named in the first
brief (§1, §4) · files carry the work, messages point (§2) · each premise with its source, checked first (§2, §3) ·
the coverage map before the briefs (§3) · steps cut by work, each ending in a commit; stop points (§4) · paid runs:
`reference/spec-depth.md` §4. What the brief adds:

1. Paid: nothing is spent before main's yes on the paid line; the launcher reads the cap from the spec and stops at
   it.
2. A window never pushes, opens a PR, edits shared docs or takes a user's decision; main's message is not approval.
3. A window never sends the user to itself: a refusal or a prompt it cannot pass goes to main with its exact text.
4. One task, one life: after «finished» the window writes its retro, reports its commit and is cleared; a fix round
   is a new life (§1, §4).
