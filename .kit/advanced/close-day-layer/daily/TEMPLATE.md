# YYYY-MM-DD

> Template for `/close-day` output. The agent fills this in at end of day. Do not edit manually.
>
> Date is in the filename — that's the load-bearing date tag for this layer. Inline `[HH:MM]` timestamps allowed within sections if useful for cross-referencing later, never required.

**Sessions:** N (≈ X hours total)
**Projects worked on:** project-a, project-b
**Experiments touched:** experiments/<name>-YYYYMMDD (if any)

## Key decisions

- Decided X because Y
- Locked the approach to Z

## Artifacts produced

- Code: feature/X merged to main
- Copy: 3 drafts for the Y campaign
- Research: market scan for Z saved to `projects/<name>/research-Z.md`

## Open threads

- Pending answer from <stakeholder> on <question>
- <task> blocked on <dependency>
- Need to revisit <decision> after seeing <data>

## Notable moments

Date is implicit (filename). Inline `[HH:MM]` only if you need to reference an exact moment later (e.g., "user reaction at [14:30]").

- User reacted strongly (positive) to <pattern> — candidate for `knowledge/concepts/`
- User rejected <thing> for the third time this week (see MEMORY for prior dates) — candidate for `.claude/rules/`
- Surprise discovery: <observation>

## Audit candidates surfaced

> Filled by `/close-day` Phase 2 audit. Each candidate cites the specific dates that triggered it (cross-reference with MEMORY.md). User verbally approves before agent writes anywhere.

- (e.g.) Pattern X observed on [2026-04-21], [2026-04-24], [2026-04-27] → propose rule `.claude/rules/copy-style.md`
- (e.g.) Topic Y across 5 daily logs → propose concept `knowledge/concepts/stripe-webhooks.md`
- (e.g.) Experiment `foo-20260322` open 36 days → ask close
