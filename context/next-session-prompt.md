# Next Session Prompt

> Agent writes this at the end of each working day via `/close-day`. You read it on session start — it tells you where we left off and what to pick up next.
>
> This is the template. First `/close-day` will overwrite it.

**Last session:** YYYY-MM-DD.

## ⚡ PICK UP HERE — immediate action

<!-- Agent writes the 1-3 highest-leverage items here, ordered. Each item date-prefixed. Usually:
     1. A concrete task in progress
     2. An unanswered question for the user
     3. Optional cleanup / follow-up -->

1. (empty — first `/close-day` populates this)

Format: `- [YYYY-MM-DD] item description (carried from N sessions ago if not new)`

## Open decisions (waiting on you)

<!-- Questions the agent needs your answer on before proceeding. Date-tag each — stale questions (>1 week) trigger an "is this still relevant?" prompt on session start. -->

- (none)

## Recent deliverables

<!-- Brief list of what actually shipped in the last 1-3 sessions. Date-tag each. Agent prunes items older than 14 days into daily/YYYY-MM-DD.md. -->

- (none)

## Active project(s)

<!-- Which `projects/<name>/` folder(s) are active right now. Agent switches on verbal command. -->

- my-first-project — guided onboarding; replace with your first real project

## Active experiments

<!-- Open `experiments/<name>-YYYYMMDD/` folders. Agent flags any older than 30 days for closure on /close-day. -->

- (none)

## Pointers to load

<!-- Files agent should read first on session start. Hooks auto-load most of these, but explicit reminders help. -->

- `CLAUDE.md` — agent identity (auto-loaded)
- `.claude/memory/MEMORY.md` — hot cache (auto-loaded)
- `projects/<active>/BACKLOG.md` — active project task queue
- `knowledge/concepts/*.md` — deep reference articles (loaded on description match)

---

## Usage

- Read this file FIRST on every session start
- Pick up from the topmost immediate-action item
- Items >1 week old without progress: ask user whether to drop them
- Items >30 days old in experiments: ask user whether to close
- Never edit this file by hand — tell the agent what's changed and let it revise
- Every entry must be date-prefixed `[YYYY-MM-DD]` — this enables stale-detection and `/close-day` audit
