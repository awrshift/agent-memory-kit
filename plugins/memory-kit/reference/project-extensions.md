---
created: 2026-08-27
last-reviewed: 2026-11-11
---

# Project extensions — when a repeated workflow earns a file

The kit ships behaviour; your repository is allowed its own. This is the decision table for
what shape a project-specific addition takes, and where it goes. Wrong shape is the expensive
part: a rule that should have been a skill costs context in every future session forever.

## Which shape

| The thing you keep re-explaining | Shape | Path | Cost when idle |
|---|---|---|---|
| "always X / never Y", mechanical, greppable | rule | `.claude/rules/<name>.md` | **every session, forever** |
| "when we do Z, these are the steps" | skill | `.claude/skills/<name>/SKILL.md` | its `description` only |
| "this must happen automatically, without asking me" | hook | `.claude/settings.json` + a script | one process per event |
| "spawn a worker with this standing brief" | agent | `.claude/agents/<name>.md` | its `description` only |
| "what is X and why is it like that" | concept | `knowledge/concepts/<topic>.md` | nothing until read |

The ordering is deliberate: **prefer the cheapest layer that actually prevents the problem.**
A rule is the most expensive shape in the kit and the only one that cannot be forgotten — spend
it on constraints that are stable for months, and keep the file at the size of the invariants
themselves (`templates/rule-template.md`).

## The three questions before you add anything

1. **Did it happen three times?** Once is an incident, twice is a coincidence. The same
   discipline as memory promotion — repetition makes a CANDIDATE, not a law.
2. **Would a deterministic check do it instead?** A grep gate, a lint rule, a CI step costs zero
   LLM context and fires forever. Automation beats instruction whenever the check is decidable.
3. **Who is the consumer?** A layer nobody reads and nothing invokes is the bloat the
   anti-bloat lens deletes. Name the trigger before you write the file.

Before writing your own, read what one project already wrote, each line with its condition and proof:
`review-classes.md` (review checklist lines) · `measurement-lessons.md` (rules for counting and model readers) ·
`reporting.md` (how reports to the user read).
After an install or an upgrade, which of the kit's practices to take as is, adapt or skip: `adoption.md`.

## Measured and not built — read before adding a gate

One project measured these ideas on its own history in 2026-11 and built none of them. Small samples, one team:
repeat a study only when your defects look different from the ones described.

- **A separate «write the tests and checks before the code» step.** Six units: a proof list written blind from the
  spec could have detected the first-return defect in 2 of 6 and would have saved 0 of 6 review rounds. Both catches
  were READS — the spec against the code at its base, the spec against itself — so the cheap form is that read.
- **A script gate on «a claim made without its check».** 98 registered rows of that kind: a script could have caught
  12, and only 1 of those was found by the outside reviewer. Most are semantic.
- **Detecting a patch from the code.** «The same place was edited again» flagged 16 of 20 correct fixes; «the diff
  holds a literal» missed 3 of 9 known patches. What did work is a line the fix spec must carry: its defect family,
  and from the third class the general rule and the layer that owns it (`review-loop.md` §0, the stop signal).
- **Stopping on the count of fix rounds per defect family.** It flagged 18 of 24 correct fixes.
- **A build rule «every stage must be observable».** 18 of 18 diagnosed defects had been named from data already
  stored. No rule.
- **Moving always-loaded rules out because they «never fire».** 93 % of rule units showed use in the transcripts.
- **A guard on briefs sent by message to another session** (does the brief carry its depth line, its paid-run
  source?). Over nine days 35 of 58 sessions that built code edited it inline and never met the spawn hook — yet on
  that path 64 of 66 specs carried the line and all 6 paid runs named their parameter source. The two misses were
  short fix-round specs, which the existing hook would have passed too. The rules held without a guard
  (measured in one project, 2026-11: 2 of 66 specs, 0 of 6 paid runs missed).
- **A sweep of every hook's regexes.** A grep found no second nested repeat in the project's hooks and scripts; the
  cheaper rule is the rule that would have caught the first: a regular expression taken into a hook is timed on a
  hostile line first. A repeat inside a repeat (`(?:[#*>-]+[ \t]*)*`) quadrupled its cost every two characters of a
  marker run — 0.58 s at 24, 2.4 s at 26, against a hook timeout of 10 s — and a file with a run of 66 existed. The
  linear form `^[ \t#*>-]*Depth pass\b` agreed with it on 79 of 79 texts; one self-test case (a 60-dash line returns at
  once) now guards it (measured in one project, 2026-11: 0.58 s at 24 characters, 2.4 s at 26).

## Skeletons

A skill — the body loads only when invoked, so depth is cheap here:

```markdown
---
name: <name>
description: <what it does + the phrasings that should trigger it. This line is the
  ONLY part always in context — write it for a router, not for a human.>
allowed-tools: Read, Write, Edit   # pre-approved, not a limit; a bare Bash pre-approves every command — scope it: Bash(python3 scripts/x.py *)
---

# /<name> — <one line>

## Steps
1. ...

## What NOT to do
- ...
```

An agent — a standing worker brief. Give it the narrowest tool set that can do the job, and a
model appropriate to the task (never the orchestrator's):

```markdown
---
name: <name>
description: >
  <when to spawn this, and — as importantly — when NOT to.>
model: sonnet
tools: Read, Grep, Glob
color: cyan
---

You are a <role>. <The invariants it must not break.>
Final report shape: <raw, structured, adjudicable — it is INPUT, not a verdict.>
```

A hook — the only shape that fires without the agent deciding to. Hooks are the right answer to
"it keeps forgetting to", and the wrong answer to "it should usually":

```json
{ "hooks": { "SessionStart": [ { "hooks": [
  { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/<name>.py\"" }
] } ] } }
```

Three facts about hooks that fail silently (Claude Code docs, checked 2026-10-22):

- **One hook's output reaching the model is capped at 10,000 characters.** Over it, the model gets a
  file path and a 2,000-character preview — your hook "printed" the context and the model never saw it.
  Measure your hook's stdout with `| wc -c`; split a big one into several hooks (the kit's session start
  runs as six parts for exactly this reason), and prove delivery with a model-level probe, not stdout.
- **A failing or timed-out hook lets the action through** by default. For a hook that is a gate, set
  `"onFailure": "block"` (Claude Code 2.1.295+) — and make the script turn its own internal errors into an
  explicit decision, because a gate that cannot start would otherwise block every call. Check that the
  interpreter RUNS, not that it exists: `python3 -c 'import sys' >/dev/null 2>&1 || exit 0; …` — on macOS
  `command -v python3` finds a stub that exits 1 without the developer tools.
- **Do not wire a copy of a kit hook in your own settings.** The plugin already runs it; a local copy fires
  twice (two memory injections, two compaction blockers). Session start flags such copies.

Exit non-zero only when you mean *block*. A hook that fails noisily on an unrelated repo state
is how a project gets a permanently annoyed operator who disables the whole layer.

## Telemetry, because everything here can rot

Lens 4 of `/memory-kit:system-audit` asks one question of each of these files: **did it ever
fire?** A rule never matched, a skill never invoked, an agent never spawned across ~5 sessions
is a drop candidate — and dropping it is a finding, not a failure. Write the extension expecting
that question.

**Checks rot too.** *Applies when your project keeps check scripts that find their subject in the tree (files by
path, declarations by folder, a registry by its location).* Three lessons from one restructure of an upstream tree
(measured in one project, 2026-11: the old checks fired on 17 of 33 canary cases, the repaired ones on 33 of 33):

- **A check that derives its subject from the tree fails on an empty subject** — it never prints «ok» over nothing.
  After the restructure one check derived 0 tables where it had found 5 thirteen days earlier, and printed «ok».
  A tool that returns no output for a non-empty input is a FAIL too: a linter given a deleted path exited with no
  output, and half of a layering check went silent for the run.
- **Anchor a check by name or by declaration shape, not by a path that can move.** The same move had broken a check
  once before and was patched by hand, per path; the second time it was fixed at the layer.
- **Test a proof row by breaking the thing it proves.** One canary row matched the planted file's name, which an
  unrelated rule also printed; on a copy with the real rule removed it must read NO — after the fix it did (31 of
  33, exit 1).

When the rule set itself has grown line by line, the procedure for shrinking it is `rules-subtraction.md`.
