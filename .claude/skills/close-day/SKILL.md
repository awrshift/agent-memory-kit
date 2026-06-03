---
name: close-day
description: End-of-day audit ritual — auto-detect missed working days (commits with no daily file) and backfill them, synthesize today into a daily log, audit patterns against MEMORY.md and existing concepts/rules, propose promotions verbally, write approved patches. One call catches up the whole daily layer.
---

# /close-day — The audit ritual (with auto-backfill of missed days)

You are closing the user's working day. This is NOT just "dump today into a file". This is the **audit moment** where you inspect what the day produced, compare it against accumulated memory, and propose what should grow into the user's knowledge base or rules.

People forget to run `/close-day` every day — that's expected and fine. So this skill also **catches up**: before synthesizing today, it finds working days that have no daily log yet and offers to backfill them in the same pass. One call recovers the whole layer.

## Your goal in three phases

### Phase 0: GAP ANALYSIS — find missed days (runs first)

Before anything else, work out which days are missing a daily log. A "working day" = a day with at least one commit. A "missed day" = a working day in the recent window that has no `daily/YYYY-MM-DD.md` file yet.

```bash
TODAY=$(date +%Y-%m-%d)
WINDOW=14   # default look-back; widen only if the user asks

# Working days = dates with non-merge commits in the window
WORKING_DAYS=$(git log --no-merges --since="$WINDOW days ago" --until="tomorrow" \
  --pretty=format:"%cd" --date=short 2>/dev/null | sort -u)

# Days that already have a daily file
EXISTING=$(ls daily/*.md 2>/dev/null | xargs -n1 basename 2>/dev/null \
  | sed 's/.md$//' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort -u)

# Missed = working days with no daily file
MISSED=$(comm -23 <(echo "$WORKING_DAYS") <(echo "$EXISTING"))
```

Detection rules:
- **Window is the last 14 days, not "since the last daily."** A gap can sit anywhere in the window — an older working day might never have gotten a daily even if newer ones did.
- **Today is always a candidate** — include it if there's uncommitted work or a commit today and no `daily/$TODAY.md` yet.
- **Skip days with no real work** — a date with only merge commits or a trivial typo fix isn't worth a daily. Note it in the report and move on.
- **If more than ~7 days are missing**, pause and confirm the window with the user before backfilling — older gaps are often deliberate skips (weekends, time off).
- **No git, or a brand-new project with no commits?** Skip Phase 0 silently and just synthesize today.

If the gap set is non-empty, show it and **ask for one batch approval** before backfilling:

```
Found 3 working days with no daily log yet:
  - 2026-05-29 — 4 commits
  - 2026-05-30 — 2 commits
  - 2026-06-02 — 6 commits
Plus today (2026-06-03).

I'll reconstruct a daily for each from that day's commits + memory date-tags, then
synthesize today in full. Backfill all? (or name days to skip)
```

One "yes" → loop through Phase 1 for each approved day, then today. No per-day pauses unless the user asked.

### Phase 1: SYNTHESIZE

Create `daily/YYYY-MM-DD.md` (today's date in ISO format). Include:

- **Session count and approximate total duration.** How many times did the user start a fresh session today? Rough total time.
- **Projects worked on.** Which `projects/<name>/` were active today.
- **Key decisions made.** What did the user decide today that will shape future work?
- **Artifacts produced.** Code shipped, copy drafted, design finalized, research completed.
- **Open threads.** What's left unfinished and should be picked up next session.
- **Notable moments.** Things the user reacted strongly to (positive or negative). These are high-signal for the audit.

Format: concise, structured markdown (follow `daily/TEMPLATE.md`). This file is the chronological record. Target 200-500 words.

**For today**, use the live conversation as your source, and also update `context/next-session-prompt.md` (NSP) with the immediate-action handoff: "Tomorrow: continue X. Open questions: Y, Z."

**For a backfilled (missed) day**, you don't have the conversation — reconstruct from what git remembers:

```bash
DATE=2026-05-29   # the missed day
git log --no-merges --since="$DATE 00:00" --until="$DATE 23:59" --pretty=format:"%h %s"   # what shipped
git log --no-merges --since="$DATE 00:00" --until="$DATE 23:59" --name-only --pretty=format: | sort -u   # files touched
grep -E "\[$DATE\]" .claude/memory/MEMORY.md   # patterns captured that day
```

Then:
- **Use commit messages verbatim as the narrative.** They were written that day; trust them.
- **Don't invent.** If it's not in a commit message, a touched file, or a `[$DATE]` MEMORY entry — don't write it. A terse commit stays terse.
- **Mark it as reconstructed.** Put one line at the top of the body: `> Backfilled on YYYY-MM-DD from git history — lower detail than a same-day log; the commits are the source of truth.`
- **Don't touch NSP for past days** — only today's close-day updates the handoff.
- **Never overwrite an existing daily.** If `daily/$DATE.md` already exists, skip it.

### Phase 2: AUDIT

Now the ritual. Read:

1. **Today's daily log** (just written)
2. **`MEMORY.md`** — date-tagged patterns from prior sessions (lean on the `[YYYY-MM-DD]` prefixes — they are how you detect repetition)
3. **Existing knowledge articles** — `knowledge/concepts/*.md` (check `updated:` frontmatter to see freshness)
4. **Existing rules** — `.claude/rules/*.md` (check `last-reviewed:` frontmatter to spot stale rules)
5. **Active experiments** — list `experiments/*/` folder names; parse the `-YYYYMMDD` suffix to find any older than 30 days

**Date-arithmetic queries you should run mentally (or with grep):**
- "Did this pattern appear in MEMORY on 3+ distinct dates within the last 14 days?" → strong promotion candidate
- "Has this rule's `last-reviewed` been more than 90 days ago?" → ask user if it still applies
- "Are any experiment folders older than 30 days?" → ask user to close or revive

Compare. Look for four kinds of signals:

#### Signal A: Cross-session repetition
A pattern you noticed today matches MEMORY entries on multiple distinct prior dates. Quote the dates back to the user — that's the evidence.

**What to do:** Propose codifying it.

> "Noticed: you rejected em-dashes in short copy on [2026-04-21], [2026-04-23], [2026-04-27]. Three distinct days, no contradiction. Codify as a rule in `.claude/rules/copy-style.md` (frontmatter `created: 2026-04-27`): 'em-dash forbidden in UI copy ≤20 words'? Or as a section in `knowledge/concepts/copy-style.md` if you want the rationale alongside? I can write it — confirm."

#### Signal B: New strong preference
User expressed a clear preference today, even once, but it was emphatic. Example: "I hate blurry previews — never do that".

**What to do:** Propose adding it. If emphatic enough, propose a rule directly. Otherwise add to MEMORY.md and wait for repetition.

> "You said clearly that blurry previews are unacceptable. Even though it's the first time in this project — should we lock it in `.claude/rules/visual-quality.md` now, or save to MEMORY and wait for a repeat?"

#### Signal C: Contradiction with existing canon
Today you did something that contradicts an existing rule or concept article. Example: `concepts/design-tokens.md` says "warm palette default" but today user insisted on a cold palette for a specific page.

**What to do:** Surface the tension. Don't silently update — ask.

> "Today we built page X in a cold palette. `concepts/design-tokens.md` says 'warm palette default for editorial pages'. Is this an exception or should the rule be updated?"

#### Signal D: Article-worthy topic emerged
Today's work surfaced a topic that's been touched several times across `daily/*.md` with accumulating detail (5+ times) and the facts are stable.

**What to do:** Propose writing a `knowledge/concepts/<topic>.md` article (you write it directly on the user's "yes" — pull the rationale together from those daily logs yourself).

> "Topic 'Stripe webhook patterns' came up on [2026-04-08], [2026-04-15], [2026-04-22], [2026-04-25], [2026-04-27] — 5 distinct days across 3 weeks. Want me to write a `knowledge/concepts/stripe-webhooks.md` article that pulls together the rationale from those daily logs?"

#### Signal E: Experiment hygiene
Folders in `experiments/<name>-YYYYMMDD/` older than 30 days that haven't been closed are stale.

**What to do:** Surface them. Don't auto-close — ask.

> "`experiments/payment-provider-selection-20260322` has been open 36 days. Still active, or ready to distill and close?"

If user says close → run the **distill ritual**:
1. Lessons → `knowledge/concepts/<topic>.md`
2. Reusable code → `projects/<name>/`
3. Update EXPERIMENT.md `Status:` field to `closed-success | closed-failed | inconclusive`
4. After distillation confirmed, propose `rm -rf experiments/<name>-YYYYMMDD/` (git history retains)

If experiment patterns repeated across days but the experiment is still open — note them in MEMORY but **do NOT propose promotion to rules yet**. Experiments are sandbox; promotion happens after distillation, not from raw experiment notes.

### Phase 3: EXECUTE APPROVED PATCHES

For each signal user approved verbally:

1. **Write the patch.** Open the target file, add the new entry at the right section, or update MEMORY.md, or modify NSP — whatever was proposed.
2. **Confirm briefly to user.** "Saved."
3. **Commit mentally to what you DIDN'T approve.** If user said "not now", DON'T write it. Keep it in next session's awareness so you can propose again if pattern recurs.

### What you do NOT do

- **Don't ask user to open any file.** Never say "open the rules file and add...". Say "I'll write it — confirm?".
- **Don't promote to `.claude/rules/` casually.** Rules are forever. A pattern needs to be either: emphatic AND clearly mechanical, OR repeated 3+ times in MEMORY without contradiction. Otherwise prefer `knowledge/concepts/<topic>.md` (which can be edited later) or a longer wait in MEMORY.
- **Don't write patches without explicit verbal approval.** "yes", "ok", "go", "save it" all count. Silence or ambiguity does not — ask again.
- **Don't surface more than 3-4 candidates per `/close-day`.** Pick the most signal-rich. Overwhelming the user with proposals kills the ritual.
- **Don't repeat proposals user already rejected.** If on last week's `/close-day` user said "not now" to adding X — don't propose X again unless there's new evidence (another repetition, related pattern, etc.).

## Session definition (context for your audit)

A "session" is **one Claude context window**. As you accumulate context (~300-500k tokens of 1M), you ask user to save state and start fresh. A day can have 3-10 sessions.

When synthesizing today's daily log, include ALL sessions of the day, not just the current one. You may need to read prior NSP states or session-start hook snapshots to know what earlier sessions contained. If uncertain, ask user: "how many times did we restart today? What was in the morning session?".

## Output format

When the user types `/close-day`, respond in this shape:

```
Gap check: 2 missed working days found (2026-04-22, 2026-04-23) + today. Backfill all? yes

Backfilled daily/2026-04-22.md (from 4 commits).
Backfilled daily/2026-04-23.md (from 2 commits).
Synthesizing today...
[brief note: X sessions, projects Y, Z, key decisions]

daily/2026-04-24.md written.
NSP updated.

Audit:

1. [Signal description]
   Proposal: [what to add where]
   Add? [yes/no]

2. [Signal description]
   ...

(Waits for user response to each item)
```

After user confirms each, execute patches and confirm briefly.

## Edge cases

- **User says "cancel" or "not now" mid-ritual** — acknowledge, stop the ritual, nothing is lost. Today's daily + NSP is already saved. Audit candidates can be revisited next time.
- **Nothing notable happened today** — the audit may surface zero candidates. That's fine. Just synthesize the daily and confirm: "Quiet day, no promotion candidates. Done."
- **User wants to preview patches before approving** — show the exact text you'd write, so they can adjust wording via speech. "Was going to write: 'X'. Wording OK?".
- **Current session still has active work** — if user types /close-day mid-task, clarify: "Close out the day now, including unfinished work? Or finish first?".

## Why this ritual exists

Memory Kit's invariant: **user only talks, agent writes**. Prior versions tried to automate promotion detection with background scripts — unreliable + violated the invariant by implicitly pushing users to edit files. `/close-day` replaces that with an agent-in-the-loop ritual: the agent has full conversational context at end of day, can spot patterns a script would miss, and does the writing itself.

The user's job is to **notice what they notice** during the day's work. Yours is to **catch it and structure it**.

Auto-backfill (Phase 0) exists because the honest reality is that people skip `/close-day` on busy days — the README even says that's fine. Rather than lose those days, the ritual reconstructs them from git history on the next run, so the daily layer stays complete enough for the cross-session audit to work. Backfilled days are lower-fidelity by nature (git remembers commits, not conversations), which is why they're marked as reconstructed and never invented.
