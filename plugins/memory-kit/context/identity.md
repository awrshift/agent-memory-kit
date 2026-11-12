# Memory Kit — how you work in this repository

## Two invariants

**1 — The user talks. You write.** The user never opens `MEMORY.md`, a handoff, a rule or a
concept article. You propose in conversation, they say "yes", you write the file and say what you
wrote. If you catch yourself saying "add this to …", rephrase as "I'll write it, confirm?".

**2 — Every memory entry carries a `[YYYY-MM-DD]` tag.** Dates are what make the audit possible:
without them you cannot see that a pattern showed up on three different days, and you cannot tell
a fresh fact from a rotten one. A stored fact about the outside world (a price, an open ticket,
"the client is waiting") older than ~7 days is a hypothesis — re-check before acting on it.

## Where things live (in this repository)

| Layer | File | Answers | Loaded |
|---|---|---|---|
| Hot cache | `.claude/memory/MEMORY.md` | what repeats · where things stand | injected every session by the hook |
| Session log | `context/handoffs/<topic>-YYYY-MM-DD.md` | what happened, session by session | newest one injected; the rest on grep |
| Deep memory | `knowledge/concepts/*.md` + `knowledge/index.md` | facts and rationale by topic | index injected; articles on demand |
| Hard rules | `.claude/rules/*.md` | what must always / never happen | loaded by Claude Code itself |

Those four are the memory layers, and there is no fifth (no `wisdom/`, `playbooks/`, `patterns/`):
every extra layer is one more place a fact goes stale.

**The work's own documents are not memory.** They live per project in `projects/<name>/` — one
folder per client or product, a single-product repo has one. Its `README.md` is the map of where
that project's documents live (read it before writing one) and names its workflow tier; specs go to
`plans/YYYY-MM-DD-<slug>.md`, written from `${CLAUDE_PLUGIN_ROOT}/templates/workspace/project/SPEC-TEMPLATE.md`. A spec, a backlog or a QA
protocol never goes into `MEMORY.md`; a dated cross-session pattern never goes into a project
folder. If a repo already keeps its documents elsewhere, its project README says so and that
mapping wins.

## The caps

`MEMORY.md` is a hot cache, not an archive: **180 lines / 32 KB / 3000 chars per line**. Three
caps because line count alone misleads — content densifies into ever-longer lines while `wc -l`
stays flat. A tripped cap means run `/memory-kit:memory-audit` before other work.

- **The header is the current state**, at most 3 lines, replaced at every close — never a stack of
  "previous session" paragraphs; session detail belongs in the handoff. A project may make it one
  pointer line to the newest handoff — its session-close document wins on form.
- **Overflow leaves by promotion**: a pattern seen on 3+ distinct dates becomes a
  `knowledge/concepts/` article (facts + rationale) or a `.claude/rules/` file (a mechanical
  always/never, on a family's 3rd counted occurrence or a user's correction). Promoted entries are
  pruned from the cache.
- **One home per fact.** When a fact changes, grep its restatements and fix them in the same pass —
  a stale copy that still looks current misleads the next session.

## Depth the plugin carries (read on demand)

From the plugin's `reference/` directory, free until opened: `orchestrator-fact-check` (a report
is input, never a fact; a number from history carries its time window and build) · `spec-depth`
(depth pass, fresh-checked practice, review stake, fail branches written first, outcome over
proxy) · `review-loop` (finding triage, the diff gate, the findings-class registry) ·
`parallel-development` (fan-out, worktree isolation, one integrator) · `doc-governance` (one SSOT
per fact) · `decisions-log` (the lean ledger) · `capability-map-sweep` (the "the library already
does this" defect class) · `project-extensions` (when a repeated workflow earns a project skill /
hook / agent). Delegating to subagents: `templates/rules/orchestration.md` holds the invariants to
copy into `.claude/rules/` (a plugin cannot ship rules; `/memory-kit:setup` offers it).
Permissions are speed bumps; hooks are gates, and a gate is proven only through its exact wiring
(`reference/harness-measurement.md`). Noisy commands: `bash ${CLAUDE_PLUGIN_ROOT}/scripts/quiet.sh <cmd>`.

## What you write freely vs what needs a "yes"

- **Freely (and you say so briefly):** `MEMORY.md` entries, the session handoff.
- **Ask first:** `.claude/rules/*.md` (always loaded — every line costs context in every future
  session), `knowledge/concepts/*.md`, and any promotion. Repetition on 3 dates makes a
  candidate, not a rule.

## During the session

An observation worth keeping becomes one dated line in the hot cache — say "saved" and move on.
Keep `MEMORY.md` current as you go, not only at the close.

Reporting to the user: lead with the outcome in one plain sentence, then what you need from them.
Your working labels (ids, branch and file names, rule numbers) are yours — drop them or say in
plain words what each is. Full sentences, a technical term glossed the first time.

Close with `/memory-kit:close-session`: capture → audit for 3+-date repetition → promote on the
user's yes → replace the header → write the handoff the next session opens with.
