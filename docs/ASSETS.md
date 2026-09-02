# README assets — state and how they are made

Nine diagrams and five demo clips in `.github/assets/` carry the visual story. Their text ages with
the product. The rule: **a diagram that states a fact is a fact that has to be swept like any
other** — same discipline as the docs, and a stale panel is a lie in the most-read file.

## State (full sweep 2026-08-31 for v6.4.0 — every asset opened and read after the rebrand;
five regenerated, four kept)

> Every asset below was opened and read, not inferred. The first pass of this table marked `04`
> and `08` "true" without looking; `08` turned out to be selling `git clone` per client on the
> front page of a release that removed cloning. Look at the picture.

| Asset | State |
|---|---|
| `01-system-map-five-hosts.png` | **regenerated 2026-09-02** (was `01-system-map.png`): the agent panel now lists all five hosts (Claude Code · Cursor · Codex · Copilot · OpenCode) and the repo panel reads "YOUR FOLDER — plain markdown files", matching the page's vocabulary; everything else as below. Generated WITH the previous asset as style ref (content grew, not shrank), clean on the first try. Original 2026-08-31 for v6.4.0 — the master panel: YOU (talk bubbles) → THE AGENT → YOUR REPO (the four memory layers + the "repeats on 3+ dates → promoted" arrow + `projects/<client>/` chips) → the session loop ("tomorrow starts already knowing") → the HOOKS bar. It carries the SIMPLIFIED role of `03`, `04` (the arrow), `05` (the chips), `06` (the bar) and `08` on the front page, which is what lets those five stay as depth in the docs. Generated with NO style ref, two iterations — the first rendered the literal word "FOOTER:" from the prompt's own section label; the fix is naming layout slots in prose ("at the very bottom, one line…"), never with an uppercase label the model can transcribe |
| `02-session-loop-agent.png` | **regenerated 2026-08-31 for v6.4.0** (was `02-session-loop.png`): the actor is now "The agent", not "Claude" — twice in the card copy; everything else unchanged |
| `03-where-memory-lives.png` | verified 2026-08-31: already host-neutral ("Agent writes all of them") — kept |
| `04-promotion-agent.png` | **regenerated 2026-08-31 for v6.4.0** (was `04-promotion.png`): "Claude proposes" → "the agent proposes" in the YOUR YES caption |
| `05-multi-project-layer.png` | **regenerated 2026-08-27 for v6.2.0** (was `05-multi-client.png`): the project tree now shows what a project folder actually holds — `README.md ← the map`, `BACKLOG.md`, `plans/`, `research/`, `decisions-log.md`, `qa/`, `materials/` — and the footer states the 6.2.0 line, «Per-project = the work's own documents. Shared = the memory.» |
| `06-hooks-skills.png` | verified 2026-08-31: four hooks + eight skills still exact, no host-specific copy — kept |
| `07-orchestrated-work-spec.png` | **regenerated 2026-08-27 for v6.2.0** (was `07-orchestrated-work.png`): a new second row — «THE SPEC — a file, written before anyone fans out», `projects/<name>/plans/YYYY-MM-DD-<slug>.md`, goal · non-goals · acceptance pre-registered · the gate commands — and the three agents now fan out FROM the spec, not from the integrator. |
| `08-one-operator-five-hosts.png` | **regenerated 2026-09-02** (was `08-one-operator-any-agent.png`): the sub-line dropped "1000+ sessions · 12 months in production" (the page no longer makes that claim), "repo" → "folder" throughout, and the footer names all five hosts. Generated WITHOUT a style ref (a string was removed — lesson 3), clean on the first try. History: 2026-08-31 for v6.4.0 the footer went from "three lines in Claude Code" to "one install — Claude Code, Cursor or Codex" |
| `09-agent-qa-projects.png` | **regenerated 2026-08-31** (was `09-agent-qa.png`): footer path was still `docs/qa/README.md` — drifted since v6.2.0 moved the QA protocol to `projects/<name>/qa/README.md`; caught by looking, exactly as this file's own rule demands |
| `og-banner-this-one-asks.png` | **regenerated 2026-09-02** (was `og-banner-one-memory.png`): headline "Built-in memory / decides what to / remember. This / one asks.", sub-line "Claude Code · Cursor · Codex · Copilot · OpenCode — plain files in your folder", the four-slab stack MEMORY.md · handoffs/ · concepts/ · rules/ unchanged. Generated with NO style ref (the headline changed — lesson 3), first try clean on all 15 strings. The model drew a rounded card with a light frame; cropped 80 px per side with `sips -c`, corners probed navy. Uploaded as the repo's social preview the same day (Settings → Social preview; `og:image` verified live). Previous: regenerated 2026-08-31 for v6.4.0 (was `og-banner.png`): "claude-memory-kit / The OS layer for Claude Code" → "agent-memory-kit / One memory for every coding agent." with the host line; layer stack relabeled MEMORY.md · handoffs/ · concepts/ · rules/ (the old top layer said CLAUDE.md). Generated WITHOUT a style ref — the label substitution would have pulled the old strings back in (lesson 3 below) |

All nine are capped at 2000 px wide: the set went from ~8.7 MB to ~2.7 MB, which matters because
several of them sit above the fold.

**The `.png` files hold JPEG data.** `sips -Z 2000 in.png --out out.png` re-encodes as JPEG while
keeping the name (it warns «Output file suffix should be jpg» and is ignored); every asset in the
set has been this way since the v6 batch, and browsers render them by content sniffing. Keep it —
a true PNG of these glow-heavy panels is ~2.5 MB each, which would put the set back near 7 MB and
undo the cap. If you ever switch to real PNGs, rename the files to match, and expect the weight.

Removed in v6: `01-before-after.png` — the before/after table in the README says the same thing,
and it was the one asset drawn in a different (emoji-face) style. Still in git history.

**Embed homes (2026-09-02):** the root README carries `og-banner`, `01-system-map-five-hosts`
(after "The problem"), the four demo clips (`demo-1` under "A day with it", `demo-3` + `demo-4`
under the comparison table, `demo-2` under "Many clients"), and `07` + `09` inside the collapsed
"For builders" block; `02` moved to `docs/ARCHITECTURE.md` (the audit-ritual section) when the
open/saved clip took its slot — the
front page is written for the solo operator, the builder panels open on click. Depth panels live in `docs/ARCHITECTURE.md` (`03`, `04`, `05`, `06`,
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

## The demo recording (`demo-1…4-*.gif` + `demo-full-session.mp4`)

One take, five clips — the README shows the scene next to the claim it proves, the launch post
gets the whole session:

| Clip | Scene | Seconds · KB |
|---|---|---|
| `demo-1-open-already-knowing.gif` | "morning, where are we with Nestlé?" → answered from the handoff (it names the files it read) · "the client came back: …" → `saved:` + the dated line | 15 · ~650 |
| `demo-2-two-clients.gif` | "now IKEA, what's due this week? and Anna wants the status on Thursdays" → reads the second project, saves the schedule change | 13 · ~1,470 |
| `demo-3-wrap-up-this-one-asks.gif` | "that's all for today, wrap up" → `Skill(memory-kit:close-session)` loads from its description → `PROPOSAL:` the four-date pattern → "yes" → rule written, both backlogs updated, handoff written, `Session closed.` | 26 · ~2,840 |
| `demo-4-next-morning.gif` | new session, "what did we settle about em-dashes, and when is the IKEA status due now?" → answered from the rule + memory | 16 · ~380 |
| `demo-full-session.mp4` | all of the above, thinking time collapsed | 68 · ~2,600 |

Scene boundaries are the keystroke clusters `cut.py`'s input-band detector finds (print them
with a few lines of the same code); the clips are `ffmpeg -ss/-to` segments of the take, each
run through `cut.py` (`--hold 1.5`, the close clip `--hold 1.2 --width 850`).

A real session, not a mock-up, and not a single slash command typed: the operator talks
("morning, where are we with Nestlé?", "the client came back: …", "now IKEA…", "that's all for
today, wrap up"), the skills trigger from their descriptions, and a second session the next
morning answers from what the first one wrote. `tools/demo/seed.sh` builds `~/dev/mk-demo`
(hot cache with the em-dash pattern on three dates, one handoff, two projects, a demo
`CLAUDE.md` that asks for terse English and two marker strings, acceptEdits permissions), `tools/demo/demo.tape`
drives Claude Code through [VHS](https://github.com/charmbracelet/vhs) (`brew install vhs`),
`tools/demo/cut.py` drops the spinner frames so ~2 minutes of model time become a watchable
clip. Re-record whenever the UI, the skill's wording or the lead changes:

```bash
tools/demo/seed.sh                      # fresh folder every take — the old take's writes stay otherwise
cd /tmp && env $(env | grep -i '^CLAUDE' | cut -d= -f1 | sed 's/^/-u /') vhs ~/dev/claude-memory-kit/tools/demo/demo.tape
python3 tools/demo/cut.py demo.mp4 demo-cut        # the full session; then segment per scene, see the table
```

Lessons, each paid for once (2026-09-02):

1. **Run VHS from a shell that is NOT inside Claude Code**, or strip every `CLAUDE*` variable:
   the nested session inherits `CLAUDE_CODE_CHILD_SESSION` and runs in a reduced mode.
2. **Do not `Wait` on a word that can appear earlier.** `/rule/` matched scene 1's answer and
   the tape typed "yes" before anything was proposed. The demo `CLAUDE.md` makes the agent emit
   `PROPOSAL:` and `Session closed.`, and the tape waits on those.
3. **Claude Code asks before the first `.claude/memory` write of a session** (sensitive file,
   see `specs/claude-code.md`) — regardless of allow rules, and `auto` mode does not suppress it
   either (probed). The tape answers it between `Hide` and `Show`, so the clip does not show
   the one keystroke; D14 and the spec say it exists. Pre-accept the folder-trust dialog in
   `~/.claude.json` — `seed.sh` does.
4. **Fixed sleeps after launch, not a `Wait` on the prompt glyph**: the glyph appears before the
   input accepts keys, and the first Enter is lost.
5. **Read the frames.** `ffmpeg -vf fps=1/6` into PNGs, open them — the take that "succeeded"
   by exit code had skipped the proposal scene entirely.

## Style notes

- The Mermaid diagram in the README ("Where memory lives") can never go stale — it renders from
  text. Prefer Mermaid for structure, PNGs for the pitch.
