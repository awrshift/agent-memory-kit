# memory-kit (plugin)

Built-in memory decides what to remember. This one asks. Persistent memory for your agent as
plain files in a folder you already have.

```shell
/plugin marketplace add awrshift/agent-memory-kit
/plugin install memory-kit@memory-kit
/memory-kit:setup
```

Upgrading later — both steps, and the full `plugin@marketplace` id on the second one (the bare
name returns `Plugin "memory-kit" not found`):

```shell
claude plugin marketplace update memory-kit
claude plugin update memory-kit@memory-kit
```

## What it does at runtime

- **SessionStart** — injects the working agreement (`context/identity.md`), the discipline nudges
  that fire, session stats and per-project spec flags (`assumed` · `building > 14 d`), **the hot
  cache itself**, the newest handoff and the knowledge index. Profile depends on `source`:
  `compact` gets back exactly what compaction dropped; `resume` gets only the nudges and stats.
  One «Rails:» line appears while a root env file has no `Read` deny or an allow hands over a
  whole tool (`Bash(git *)`, `Bash(*)`) — until `/memory-kit:setup rails` runs or you decline it.
  Since 7.2 it runs as six parts (`--part 1..6`), each under Claude Code's 10,000-character cap on
  one hook's context — above the cap the model saw only a 2 KB preview, i.e. no hot cache.
- **PreCompact** — blocks compaction until `MEMORY.md` is fresh and inside its three caps
  (180 lines / 32 KB / 3000 chars per line).
- **PreToolUse(Edit|Write)** — asks before an edit that can weaken an existing test (an assertion
  line changed or removed, a `.skip`/`.only` added) and before any hand edit of a `.snap`; never
  blocks the red→green loop; `CMK_ALLOW_TEST_EDITS=1` opts out for a session.
- **PreToolUse(Bash)** — the git guard: blocks force push, `push --mirror`, `reset --hard`,
  `clean -f`, `branch -D`, `checkout .`, `restore .` wherever the flag sits in a real git command
  (never in quoted text or a commit message); `--force-with-lease` passes; `CMK_GIT_GUARD=off` opts out.
- **PreToolUse(Read|Edit|Write|Bash)** — the secrets guard (7.2): blocks reading or writing
  `.env`, `.env.local`, `.env.*.local`, `.env.production` (and development/test/staging), `*.pem`,
  `id_rsa*`, `*.p12` — by the file tools or by a shell command, inline script or redirection;
  `source` / `.`, `cp`/`ln`/`mv`, `ls`, `test`, `git`, `rm` pass, and `.env.example` is never
  secret; `CMK_SECRETS_GUARD=off` opts out.
- **SessionEnd** — timestamp logging.

In a repository that never ran `/memory-kit:setup`, the hooks inject one pointer line and write
nothing.

## Skills

| Skill | For |
|---|---|
| `close-session` | the end-of-session ritual: capture → audit for 3+-date repetition → promote on a yes → handoff |
| `memory-audit` | cap-trip surgery on the hot cache, by an approved move plan |
| `system-audit` | the periodic seven-lens sweep of the whole system, every finding evidence-backed — including the transcript profiler that answers "did this layer ever fire" and `gates.py`, which proves every PreToolUse hook through its exact wiring |
| `setup` · `tour` | adopt the kit here (`setup rails`: only the permission rails, on an adopted repo) · walk through it on your own files |
| `session-review` · `second-opinion` | adversarial review of a session · of one high-stakes decision |
| `qa-sweep` | multi-lens agent QA of a running product (needs `projects/<name>/qa/README.md`, template in `reference/`), every finding and run record bound to the spec's `AC-n` |
| `document` | the human record of a change — PR body · changelog entry · release note · postmortem — drafted only from `git diff` / `git log`, never from what the model remembers building |
| `code-sync` | after a merge: specs reconciled against the code — `building → done` on a gate you ran, `stale` with the reason, `assumed` specs listed as owed ratification, the project map and `Last verified` refreshed. Surgical edits only |

Agents: `executor` (builds to a spec file in a worktree) · `recon` (read-only facts) ·
`idea-validator` (isolated critic) · `qa` (one adversarial lens on the running app).

![](../../.github/assets/07-orchestrated-work-spec.png)
![](../../.github/assets/09-agent-qa-projects.png)

## Beyond Claude Code

The memory state is plain markdown, so any agent can follow it — with less enforcement.
Verified on Codex CLI (0.151.0): the same manifests install directly —

```shell
codex plugin marketplace add awrshift/agent-memory-kit
codex plugin add memory-kit@memory-kit
```

— and all 10 skills appear as `memory-kit:<name>`. GitHub Copilot CLI installs the same way
(`copilot plugin marketplace add` + `copilot plugin install memory-kit@memory-kit` — all 10
skills load). On Cursor,
`cursor-agent plugin marketplace add <git-url>` indexes the same manifests, `--plugin-dir`
loads all 10 skills, and the CLI executes the SessionStart hook — injection works there.
Hosts that don't run the hooks lose the automatic injection and the PreCompact block;
`/memory-kit:setup` offers the replacement — an `AGENTS.md` protocol block
(`templates/workspace/AGENTS-MEMORY-PROTOCOL.md`) that hands them the same discipline as an
always-loaded instruction. **OpenCode** goes further: the repo ships a real plugin for it
(`.opencode/plugins/memory-kit.js`, one `opencode.json` line) that injects memory into every
model call, compaction-proof. What each host honours, probe by probe: the kit repository's
[`docs/specs/`](https://github.com/awrshift/agent-memory-kit/tree/main/docs/specs) (not part
of the installed plugin).

## State it owns in your repository

Shared memory: `.claude/memory/MEMORY.md` · `context/handoffs/` · `knowledge/` · `.claude/rules/`.
Per project: `projects/<name>/` — `README.md` (the map of where that project's documents live,
plus the workflow tier), `BACKLOG.md`, `plans/` (specs executors build to, including a
`plans/*-assumed.md` when an executor was told to build past a missing decision), `research/`,
`decisions-log.md`, `review-findings.md`, `qa/`, `materials/`. Everything past the first two
appears on first use. `document` writes outside that tree, where a human looks for it:
`CHANGELOG.md` at the repo root, `docs/releases/`, `docs/postmortems/` — or wherever the
project README's map already sends that class.

## Environment knobs

`CMK_INJECT_BUDGET` (48000) · `CMK_MEMORY_LINE_CAP` (180) · `CMK_MEMORY_BYTE_CAP` (32768) ·
`CMK_MEMORY_MAXLINE_CAP` (3000) · `CMK_ALLOW_TEST_EDITS`.

Architecture and rationale: the kit repository's
[`docs/ARCHITECTURE.md`](https://github.com/awrshift/agent-memory-kit/blob/main/docs/ARCHITECTURE.md).
