<!-- from one project's practice, in trial since 2026-11; count due 2026-11-25; see reference/window-cycle.md -->
<!-- Applies when: you run more than one session at a time — one main session and windows that build or measure. -->

# <window name> — brief: <task, one line>

The main session fills the block, saves it as a file the window reads (beside the task's spec), and sends the window
one message that points at that file. The procedure behind every line: the plugin's `reference/window-cycle.md`.

```
Window <name> — task: <one line>. Reports to <the main session's listed name>.
Spec (the contract): <path> (commit <hash>). Worktree <path>, branch <name> at <head hash>.
Stop points: <each decision point where the window stops and waits for the main session>.
Premises: <each fact about code, data, a time or a run this brief states — with the source it was read from>.
Paid: none | the spec's paid line (<section>): units, cost and cap are read there.
Slot: <the shared resource this window may use — port, database, account> (only if the project shares resources).
Steps: <the task's steps, each ending in a commit>.
Done = <the gate>; report = a committed file at <path>; message to main ≤ 5 lines:
  verdict · report path · commit · what main must decide.
```

The rules behind the lines live in `reference/window-cycle.md`: one task per window, the second named in the first
brief (§1, §4) · files carry the work, messages point (§2) · each premise with its source, checked first (§2, §3) ·
the coverage map before the briefs (§3) · steps cut by work, each ending in a commit; stop points (§4) · paid runs:
`reference/spec-depth.md` §4. What the brief adds:

1. Paid: nothing is spent before main's yes on the spec's paid line; the run script reads the cap from the spec and
   stops at it.
2. A window never pushes, opens a PR, edits shared docs or takes a user's decision; main's message is not approval.
