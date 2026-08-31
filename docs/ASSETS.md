# README assets — state and how they are made

Nine diagrams in `.github/assets/` carry the visual story. They are PNGs, so their text ages with
the product. The rule: **a diagram that states a fact is a fact that has to be swept like any
other** — same discipline as the docs, and a stale panel is a lie in the most-read file.

## State (full sweep 2026-08-31 for v6.4.0 — every asset opened and read after the rebrand;
five regenerated, four kept)

> Every asset below was opened and read, not inferred. The first pass of this table marked `04`
> and `08` "true" without looking; `08` turned out to be selling `git clone` per client on the
> front page of a release that removed cloning. Look at the picture.

| Asset | State |
|---|---|
| `01-system-map.png` | **new 2026-08-31 for v6.4.0** — the master panel: YOU (talk bubbles) → THE AGENT (Claude Code · Cursor · Codex) → YOUR REPO (the four memory layers + the "repeats on 3+ dates → promoted" arrow + `projects/<client>/` chips) → the session loop ("tomorrow starts already knowing") → the HOOKS bar. It carries the SIMPLIFIED role of `03`, `04` (the arrow), `05` (the chips), `06` (the bar) and `08` on the front page, which is what lets those five stay as depth in the docs. Generated with NO style ref, two iterations — the first rendered the literal word "FOOTER:" from the prompt's own section label; the fix is naming layout slots in prose ("at the very bottom, one line…"), never with an uppercase label the model can transcribe |
| `02-session-loop-agent.png` | **regenerated 2026-08-31 for v6.4.0** (was `02-session-loop.png`): the actor is now "The agent", not "Claude" — twice in the card copy; everything else unchanged |
| `03-where-memory-lives.png` | verified 2026-08-31: already host-neutral ("Agent writes all of them") — kept |
| `04-promotion-agent.png` | **regenerated 2026-08-31 for v6.4.0** (was `04-promotion.png`): "Claude proposes" → "the agent proposes" in the YOUR YES caption |
| `05-multi-project-layer.png` | **regenerated 2026-08-27 for v6.2.0** (was `05-multi-client.png`): the project tree now shows what a project folder actually holds — `README.md ← the map`, `BACKLOG.md`, `plans/`, `research/`, `decisions-log.md`, `qa/`, `materials/` — and the footer states the 6.2.0 line, «Per-project = the work's own documents. Shared = the memory.» |
| `06-hooks-skills.png` | verified 2026-08-31: four hooks + eight skills still exact, no host-specific copy — kept |
| `07-orchestrated-work-spec.png` | **regenerated 2026-08-27 for v6.2.0** (was `07-orchestrated-work.png`): a new second row — «THE SPEC — a file, written before anyone fans out», `projects/<name>/plans/YYYY-MM-DD-<slug>.md`, goal · non-goals · acceptance pre-registered · the gate commands — and the three agents now fan out FROM the spec, not from the integrator. |
| `08-one-operator-any-agent.png` | **regenerated 2026-08-31 for v6.4.0** (was `08-one-operator-many-projects.png`): footer "three lines in Claude Code" → "one install — Claude Code, Cursor or Codex"; top-right card "one install → new repo" |
| `09-agent-qa-projects.png` | **regenerated 2026-08-31** (was `09-agent-qa.png`): footer path was still `docs/qa/README.md` — drifted since v6.2.0 moved the QA protocol to `projects/<name>/qa/README.md`; caught by looking, exactly as this file's own rule demands |
| `og-banner-one-memory.png` | **regenerated 2026-08-31 for v6.4.0** (was `og-banner.png`): "claude-memory-kit / The OS layer for Claude Code" → "agent-memory-kit / One memory for every coding agent." with the host line; layer stack relabeled MEMORY.md · handoffs/ · concepts/ · rules/ (the old top layer said CLAUDE.md). Generated WITHOUT a style ref — the label substitution would have pulled the old strings back in (lesson 3 below) |

All nine are capped at 2000 px wide: the set went from ~8.7 MB to ~2.7 MB, which matters because
several of them sit above the fold.

**The `.png` files hold JPEG data.** `sips -Z 2000 in.png --out out.png` re-encodes as JPEG while
keeping the name (it warns «Output file suffix should be jpg» and is ignored); every asset in the
set has been this way since the v6 batch, and browsers render them by content sniffing. Keep it —
a true PNG of these glow-heavy panels is ~2.5 MB each, which would put the set back near 7 MB and
undo the cap. If you ever switch to real PNGs, rename the files to match, and expect the weight.

Removed in v6: `01-before-after.png` — the before/after table in the README says the same thing,
and it was the one asset drawn in a different (emoji-face) style. Still in git history.

**Embed homes (final for 2026-08-31):** the root README carries `og-banner`, `01-system-map`
(after "The problem"), `02`, `07`, `09` — every CONCEPT is on the front page, with the map as
the simplified umbrella. Depth panels live in `docs/ARCHITECTURE.md` (`03`, `04`, `05`, `06`,
`08`) and `plugins/memory-kit/README.md` (`07`, `09` again). The no-orphan CI check counts
embeds across all markdown, so a future trim must re-home or delete the asset, never just
drop the reference. (The `01` slot previously belonged to `01-before-after.png`, removed in
v6 — the new map is unrelated to it.)

Asset filenames change when their content changes. GitHub's camo proxy caches images by URL, so
an in-place overwrite keeps serving the old picture to everyone who already loaded the page —
renaming is the only reliable cache bust.

## How to regenerate one

Generated with Google's image models via the REST API — `gemini-3-pro-image` (Nano Banana Pro)
is the one to use for these: the panels are text-dense and the Pro model is the one that renders
long strings without drifting. Pass the CURRENT asset as a style reference so the new panel
matches the set, and give the prompt the **complete text spec**, every string verbatim.

```bash
# GOOGLE_API_KEY from your environment; model default is gemini-3-pro-image
python3 tools/genimg.py .github/assets/06-hooks-skills.png prompt.txt out.png
sips -Z 2000 out.png          # keep the set under control
```

Two lessons from doing this, both cheap to repeat and expensive to skip:

1. **"Reproduce this exactly, change only the footer" produces typos.** That prompt shape drifted
   `merges`→`marges`, `silent`→`siient`, `401/403/404`→`401/409/404`, `pollable`→`poliable`.
   Rewriting the same request as a full content spec — every string listed, plus an explicit
   spelling-check list of the words that had drifted — came back clean on the first try.
2. **Read the generated image before committing it.** Every one of those typos was invisible in
   the file size and the API response, and obvious in two seconds of looking.
3. **When the content SHRINKS, drop `--ref`.** Removing two skills from `06` failed twice with a
   style reference attached: the model kept re-drawing the deleted `memory-lint` entry it could
   see in the reference, and an explicit "never render this string" instruction did not stop it.
   Describing the style in prose, with no reference image, produced the right eight on the first
   try. A reference image is authoritative for what to KEEP, not for what to remove.

The prompt files used for the v6 batch are not kept — the spec they encode is this file's state
table plus the copy already visible in each asset.

## Style notes

- The Mermaid diagram in the README ("Where memory lives") can never go stale — it renders from
  text. Prefer Mermaid for structure, PNGs for the pitch.
