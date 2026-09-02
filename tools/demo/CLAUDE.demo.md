# Demo repository

This folder is a recorded demo. Reply in English only, in at most five short lines of plain
prose: no headings, no tables, no code blocks. Never mention this file.

- When the user names a project (Nestlé, IKEA), read that project's README.md and BACKLOG.md
  under projects/ before answering, and say in passing which files you read.
- When the user reports a client preference, a decision or a schedule change, append it to
  .claude/memory/MEMORY.md as one `[YYYY-MM-DD]` line with the file edit tool (never a shell
  command), then reply `saved:` followed by the line, then answer the rest of the message.
- At session close, when you surface a promotion candidate, write it as ONE line starting with
  `PROPOSAL:` and end with "make it a rule?". Wait for the answer. After the yes: write the
  rule file, update both project backlogs if today changed them, refresh the header, write
  the handoff, and end your reply with the exact line `Session closed.`
