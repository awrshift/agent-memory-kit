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
Paid: none | <N units>, ~<cost> from <script output file>, cap <cap>.
Slot: <the shared resource this window may use — port, database, account> (only if the project shares resources).
Size: <the task's estimate> · main's context at send: <N> k.
Done = <the gate>; report = a committed file at <path>; message to main ≤ 5 lines:
  verdict · report path · commit · context: <the number /context prints> · what main must decide.
```

Notes, one line each:

1. One task per window; a second task is named in the first brief, so a cleared window restarts from files.
2. Files carry the work, messages point: the report is a committed file, the message only points at it.
3. A premise carries a source read this session — a memory, handoff or report line is a pointer, not a source.
4. The window checks each premise first; a wrong one goes back to main in the next message, with its evidence.
5. Size: one deliverable that reaches «done» in about 150k tokens of the window; a bigger task stops after each step.
6. At every stop the window gives its context as the number `/context` prints, never an estimate.
7. A window takes a next task only while its context plus the task's estimate stays within about 250k.
8. Paid: nothing is spent before main's yes on that line; the run script reads the cap from the brief and stops at it.
9. A window never pushes, opens a PR, edits shared docs or takes a user's decision; main's message is not approval.
10. Before the briefs, main commits a coverage map: every stage of the source → its owner, or «not taken because …».
