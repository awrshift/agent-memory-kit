![Claude Memory Kit](.github/assets/og-banner.png)

# Claude Memory Kit

**Your Claude remembers everything. Every client, every brief, every decision. Across sessions. Zero setup.**

[![Version](https://img.shields.io/github/v/release/awrshift/claude-memory-kit?label=version&color=brightgreen)](https://github.com/awrshift/claude-memory-kit/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-6366f1)](https://docs.anthropic.com/en/docs/claude-code/overview)

## The problem

Every time you open Claude, it forgets everything. Yesterday you locked the brand voice. Today
you have to explain it again. Last week it helped you find the right campaign angle — this week
you can't remember exactly how.

The first 10 minutes of every session go to re-explaining what Claude **already knew**.

**Memory Kit fixes this. Free. Runs on top of your Claude Pro or Max subscription.**

## Quick start

```bash
git clone https://github.com/awrshift/claude-memory-kit.git my-projects
cd my-projects
claude
```

That's it. Claude sets itself up and asks a couple of questions (your name, what you're working on).

> [!TIP]
> Say `/tour` after install — Claude walks you through the system using your own files.

---

## Before / after

![](.github/assets/01-before-after.png)

| | Without Memory Kit | With Memory Kit |
|---|---|---|
| **New session** | "What were we working on?" | Opens with last session's handoff already loaded |
| **After 10 sessions** | Nothing accumulates | Searchable base of decisions, tones, patterns |
| **Multiple clients** | Chaos | Each client has its own folder, everything in place |
| **Context compaction** | Silently loses data | Hook blocks compaction until state is saved |
| **Memory bloat** | Grows until useless | Three size caps, watched automatically every session |

---

## How a session works

![](.github/assets/02-daily-workflow.png)

Three steps. That's the entire workflow:

### 1. Open a session
Claude auto-loads context: the **handoff** (the note the previous session left), memory health
stats, your projects, the knowledge index. You do nothing — you just see "here's where we left
off" and continue.

### 2. Work as usual
Talk to Claude. Write copy. Do research. Lock the tone. When something worth keeping comes up,
Claude saves it as a dated one-liner and tells you "saved". Safety hooks run silently — they
prompt a save every ~50 messages and physically block context compaction until state is written.

### 3. Close the session
Say `/close-session`. Claude **doesn't just** dump logs — it audits: "noticed you rejected
em-dashes on three different dates — make it a tone-of-voice rule?" You say "yes", it writes.
Then it leaves a handoff note for tomorrow-you. **Tomorrow's session opens with that note
already loaded.**

---

## Where memory lives

![](.github/assets/03-memory-layers.png)

Four places, each answering a different question. Claude writes all of them — you only talk.

| Layer | Answers | Written |
|---|---|---|
| `.claude/memory/MEMORY.md` | "what patterns repeat" + "where things stand" | while you talk |
| `context/handoffs/*.md` | "what happened, session by session" | at `/close-session` |
| `knowledge/concepts/*.md` | "facts and rationale by topic" | after your "yes" |
| `.claude/rules/*.md` | "what must always / never happen" | after months of stable pattern |

**A pattern's journey:** noticed in conversation → saved as a dated line in MEMORY →
repeats on 3+ dates → Claude proposes promotion → your "yes" → becomes a knowledge article or
a rule, and the raw lines are pruned. Observation → candidate → law. You approve every step.

![](.github/assets/04-promotion-pipeline.png)

---

## Why it doesn't rot (v5)

Memory systems don't usually die loudly — they rot quietly: a "current state" file that froze
three weeks ago but still looks authoritative; a memory file that grew so dense it's unreadable.
v5 is built around the failure modes we hit in real long-running use:

- **Three size caps on MEMORY.md** (180 lines / 32 KB / 3000 chars per line), checked by a hook
  at every session start. Three, because line count alone lies — content can densify into
  ever-longer lines while the line count stays flat. When a cap trips, the session opens with
  an audit prompt instead of silently growing.
- **Handoffs instead of a rolling status file.** One immutable note per closed session; the
  newest one is injected automatically. A note that says its date can't pretend to be current.
- **Stale-reference detector.** Every session start, file paths mentioned in memory are checked
  against disk; anything that moved or vanished is flagged. A memory that references dead files
  is the #1 way agents confidently act on outdated beliefs.
- **The header rule.** The top of MEMORY.md is "current state in 2-3 sentences", *replaced* at
  every close — never a stack of "previous session" paragraphs.

---

## Multiple clients

![](.github/assets/05-multi-project.png)

Each client = their own folder. Shared layers (rules, memory, wiki) load for every project.
Per-project materials load when you name the project.

Say "we're working on Nestlé" — Claude unloads other clients and loads that scope only.

---

## Hooks and operators

![](.github/assets/06-hooks-and-operators.png)

Five hooks run silently — they make state survive compaction and crashes, and they watch the
memory caps. Two slash operators give you direct control: `/close-session` (the end-of-session
ritual) and `/tour`. Power-user extras (search, hygiene, usage stats, and an optional day-by-day
journal layer with `/close-day`) sit in `.kit/advanced/` for when you want them.

Everything in plain text files. No databases. No external services. `git checkout` restores anything.

---

## FAQ

<details>
<summary><b>I'm not a programmer. Will this work?</b></summary>

Yes. You talk to Claude in plain language. "Read the client brief and propose three newsletter
topics" — works. Install is one command. You never edit the memory files yourself — that's the
kit's first rule: *you only talk, Claude writes*.

</details>

<details>
<summary><b>How much does it cost?</b></summary>

The kit itself is free, open source. You need a Claude Pro or Max subscription (which you
probably already have). No additional cost.

</details>

<details>
<summary><b>Is my data private?</b></summary>

Yes. Everything is stored on your computer in plain text files. Nothing leaves. Handoffs and
memory are gitignored by default, so they stay private even if you push the repo.

</details>

<details>
<summary><b>Can I use it with an in-progress project?</b></summary>

Yes. On install, tell Claude you already have a project — it analyses it and integrates.

</details>

<details>
<summary><b>What if I forget to run /close-session?</b></summary>

Nothing breaks. Safety hooks save progress automatically every ~50 messages and before any
context compaction. `/close-session` is the cherry on top — the deliberate audit where patterns
get promoted to permanent knowledge and the handoff note gets written.

</details>

<details>
<summary><b>What if I accidentally break a memory file?</b></summary>

Everything is in git. `git checkout .claude/memory/` reverts in a second.

</details>

<details>
<summary><b>I liked the daily journal (/close-day) from v4. Where did it go?</b></summary>

It's an opt-in layer now: `.kit/advanced/close-day-layer/` — one `cp` command enables it, and it
composes with the v5 core (journal + handoffs together). It left the default because in
long-running use the chronicle was the layer that silently rotted when you skipped days. Full
story: that folder's README.

</details>

<details>
<summary><b>What if I'm migrating from v4?</b></summary>

Clone v5 into a new folder and tell Claude: "I have a v4 kit at &lt;path&gt;, help me migrate".
Your memory entries, knowledge articles, rules and projects carry over as-is; the mechanical
steps are in [.kit/CHANGELOG.md](.kit/CHANGELOG.md) § Migration.

</details>

---

## What's inside

```
README.md               ← You are here
LICENSE                 ← MIT
CLAUDE.md               ← Agent's brain — who it is, how it works
SKILL.md                ← Metadata for skill aggregators
projects/               ← Real client / product folders (tasks + materials)
experiments/            ← Sandbox for hypotheses + prototypes (date-named)
knowledge/              ← Knowledge base (grows over time)
context/handoffs/       ← One note per closed session (private by default)
.claude/                ← Kit core: memory, hooks, skills, rules
.kit/                   ← Docs about the kit ITSELF (architecture, changelog,
                          contributor guide) + advanced/ (opt-in layers:
                          power commands + the daily-journal layer)
```

**`projects/` vs `experiments/`** — `projects/<name>/` for real client work (polished,
indefinite lifetime, patterns promote to rules); `experiments/<name>-YYYYMMDD/` for hypotheses
and prototypes (rough OK, days-to-weeks lifetime, distill on close, then delete). Full spec:
[`experiments/README.md`](experiments/README.md).

**Full architecture:** [.kit/ARCHITECTURE.md](.kit/ARCHITECTURE.md)
**Version history:** [.kit/CHANGELOG.md](.kit/CHANGELOG.md)
**Contributing:** [.kit/CONTRIBUTING.md](.kit/CONTRIBUTING.md)

---

## Origin

Ideas from [Andrej Karpathy](https://karpathy.ai/) and [Cole Medin](https://github.com/coleam00).
Rebuilt around Anthropic-native Claude Code primitives.

800+ real sessions across 8+ projects. v5 is what survived all the iterations — including the
parts we had to retire because they rotted in our own production use.

## Help

Issues and PRs welcome. See [.kit/CONTRIBUTING.md](.kit/CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
