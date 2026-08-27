---
created: 2026-08-27
last-reviewed: 2026-08-27
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

## Skeletons

A skill — the body loads only when invoked, so depth is cheap here:

```markdown
---
name: <name>
description: <what it does + the phrasings that should trigger it. This line is the
  ONLY part always in context — write it for a router, not for a human.>
allowed-tools: Read, Write, Edit, Bash
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

Exit non-zero only when you mean *block*. A hook that fails noisily on an unrelated repo state
is how a project gets a permanently annoyed operator who disables the whole layer.

## Telemetry, because everything here can rot

Lens 4 of `/memory-kit:system-audit` asks one question of each of these files: **did it ever
fire?** A rule never matched, a skill never invoked, an agent never spawned across ~5 sessions
is a drop candidate — and dropping it is a finding, not a failure. Write the extension expecting
that question.
