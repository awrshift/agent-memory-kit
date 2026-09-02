---
created: 2026-09-02
last-reviewed: 2026-09-02
---

# Distribution — how the kit reaches people

> The plan, not the log. One page, dated, revised when a number changes. Companion to
> `DECISIONS.md` (what needs the maintainer) and `specs/` (what each host honours).

## Who we are talking to

**Primary:** a solo operator who runs several clients through an agent in a terminal every
day — marketing, research, content, some product work — and is not paid to write code. Types
a handful of commands once, then only talks. Reached where Claude Code users gather, because
that is where they already are; "non-programmer" is a description of their job, not of their
comfort with a terminal.

**Secondary:** builders orchestrating subagents. They find the collapsed section; nothing on
the front page is written for them.

## The one-line promise and its proof

"Built-in memory decides what to remember. This one asks." Proof, in order of strength:

1. The comparison table on the front page — every row is checkable against the vendor's docs.
2. `git diff` on a memory file: the thing no built-in and no database tool can show.
3. The measured session-start cost (2–4k tokens, ceiling ~12k) against the 2026 complaint of
   30–40k at session start.
4. The changelog: seven layers retired because they rotted, the year-long "always loaded" bug
   found and fixed, CI checking injection on every push. Credibility for practitioners; keep it
   in the Origin section and the launch post, not the hero (D8).

Claims we do not make: "doesn't rot" as an absolute (staleness is *visible*, not impossible —
nothing detects a wrong-but-fresh belief); any star count; "one memory for every agent" as
the lead (claude-mem lists more hosts, and auto-capture; our wedge is approval and files).

## Channels, in the order they pay

| # | Channel | Why | Cost | Status |
|---|---|---|---|---|
| 1 | **Feedback loop first** — the first-week issue template, the README ask, setup ending with one question | Zero feedback has ever arrived; traffic sent before this exists is wasted | done 2026-09-02 (template + ask); setup question open | ✅ / open |
| 2 | **Anthropic community marketplace** (`clau.de/plugin-directory-submission`, a web form + automated security scan; PRs auto-closed) | The largest discovery surface, and it serves Cowork too — see D13 for what Cowork users get | one form, one week of self-use on the current layout first (D2) | open |
| 3 | **A 30-second recording** — session opens already knowing → "saved" → `/close-session` proposes a rule → next session | The system map explains; a recording convinces. Replaces no diagram, sits under "A day with it" | asciinema or a GIF, one afternoon | open |
| 4 | **Launch post** — the honest hook: "my agent's memory file was never loaded for a year, here is how I found out". Show HN, r/ClaudeAI, r/ClaudeCode, X | The bug story is more credible than a feature list — and half the room will read it as "shipped broken for a year"; write that top comment first and answer it inside the post | half a day; post only after 1–3 | open |
| 5 | **Cursor central marketplace** | Application submitted 2026-08-31, no SLA | waiting | ⏳ |
| 6 | **Russian-language long-form** (post or video) | The maintainer's native language, a solo-operator audience with few resources on Claude Code, low competition | one piece, after 4 | open |
| 7 | awesome-claude-code / awesome-agents-md lists | Cheap, slow, no signal back; last | two PRs | last |

## What to measure, weekly

| Metric | Where | Trust |
|---|---|---|
| Unique visitors, referrers | GitHub Insights → Traffic | high — humans |
| Stars, forks | repo | medium — vanity, but a real person clicked |
| **Unique cloners** | Traffic → Clones | **low until segmented**: 443 unique cloners against 52 visitors in 14 days (2026-08-18 → 09-01) is the signature of loaders and crawlers (the OpenCode git+ install re-clones; marketplace catalogs poll), not of humans deciding to try. Do not quote it as adoption. |
| First-week issues opened | Issues, label `feedback` | the only metric that says whether it worked for someone |
| Marketplace installs | the marketplace's own counter, once listed | high |

## What we are not doing

- No paid promotion, no newsletter, no Discord. One maintainer; every channel above is a
  file or a post, not a commitment to answer daily.
- No benchmark theatre. If a memory benchmark is ever run, it is run against the kit's own
  claim (a stale fact is visible), not against retrieval scores the kit does not compete on.
- No rename. `Memory Kit` on the page, `memory-kit@memory-kit` at install,
  `agent-memory-kit` as the repository — three strings, one already-settled decision (D3).
