# Privacy

Memory Kit collects nothing. It has no server, no account, no analytics and no telemetry, and no
hook or script in the plugin opens a network connection.

- **What it stores:** the memory you approve — `MEMORY.md`, handoffs, knowledge articles, rules —
  as plain files in your own repository, plus a session counter and logs in `.claude/state/`.
  They stay there until you delete them; nothing is copied anywhere else.
- **What it reads:** files in the repository you work in, your Claude Code settings files, and —
  only when you run `/memory-kit:system-audit` — this repository's session transcripts in
  `~/.claude/projects/`. Results stay in your conversation.
- **What leaves your machine:** only what your agent already sends to its model provider as part
  of the session. `/memory-kit:second-opinion` can hand a review brief to another model only
  through a tool you configured yourself; the plugin ships no such client.

Details of every hook: [`plugins/memory-kit/README.md`](plugins/memory-kit/README.md#what-it-reads-writes-and-sends).
Questions: [open an issue](https://github.com/awrshift/agent-memory-kit/issues).
