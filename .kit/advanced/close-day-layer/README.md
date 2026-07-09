# Daily-chronicle layer (opt-in since v5.0)

The v4 kit kept a per-day journal (`daily/YYYY-MM-DD.md`) written by the `/close-day` ritual,
plus a rolling `context/next-session-prompt.md` (NSP). **v5.0 replaced both defaults** with the
lean core: per-session handoffs (`context/handoffs/`) + the `/close-session` audit. Why: in
long-running production use the chronicle layer was the part that silently rotted — days went
unclosed, the NSP froze while looking authoritative, and memory grew past its caps unnoticed.
The handoff protocol has one artifact per closed session and the hook always injects the newest
one, so "stale but authoritative-looking" can't happen.

**Keep this layer if you genuinely want a day-by-day journal** (some users do — it reads like a
work diary and `/close-day` can backfill missed days from git history).

## Enable

```bash
# from the kit root
cp -r .kit/advanced/close-day-layer/skills/close-day .claude/skills/close-day
mkdir -p daily && cp .kit/advanced/close-day-layer/daily/README.md .kit/advanced/close-day-layer/daily/TEMPLATE.md daily/
```

Then use `/close-day` at end of day as before. It composes fine with the v5 core: `/close-day`
writes the journal; `/close-session` still owns the audit + handoff. (The old NSP template is
kept here as `next-session-prompt-TEMPLATE.md` for reference only — the hook no longer reads it.)

## Contents

- `skills/close-day/SKILL.md` — the full end-of-day ritual (synthesis, gap backfill, promotion audit)
- `daily/TEMPLATE.md` + `daily/README.md` — the journal format
- `next-session-prompt-TEMPLATE.md` — the retired NSP format (historical reference)
