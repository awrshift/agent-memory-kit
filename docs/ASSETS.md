# README assets — state and how they are made

Nine diagrams in `.github/assets/` carry the visual story. They are PNGs, so their text ages with
the product. The rule: **a diagram that states a fact is a fact that has to be swept like any
other** — same discipline as the docs, and a stale panel is a lie in the most-read file.

## State (03, 05 and 07 swept 2026-08-27 for v6.2.0 — the three the project layer touches;
the rest carry their v6 / v6.1 state)

> Every asset below was opened and read, not inferred. The first pass of this table marked `04`
> and `08` "true" without looking; `08` turned out to be selling `git clone` per client on the
> front page of a release that removed cloning. Look at the picture.

| Asset | State |
|---|---|
| `02-session-loop.png` | regenerated for v6 (injection carries the hot cache; the ~50-message auto-save prompt is gone) |
| `03-where-memory-lives.png` | regenerated for v6 (hot cache marked *injected every session*; namespaced skill) |
| `04-promotion.png` | regenerated for v6 (the namespaced skill in the YOUR YES step) |
| `05-multi-client.png` | opened 2026-08-27: the panel draws `projects/nestle/` as `BACKLOG.md` + `brand-guide.pdf` + `tone-of-voice.md`, and its footer «Per-project = projects/<name>/. Shared = everything else» is exactly 6.2.0's line. **Incomplete, not wrong:** the folder now also holds `README.md` (the map), `plans/`, `research/`, `decisions-log.md`, `review-findings.md`, `qa/`. Regenerate when the next batch runs. |
| `06-hooks-skills.png` | regenerated for v6.1 — four hooks, the eight remaining skills |
| `07-orchestrated-work.png` | opened 2026-08-27: still true — «builds to an already-decided spec in an isolated git worktree» says nothing about where the spec lives, so 6.2.0 contradicts nothing. **Incomplete, not wrong:** the panel never shows that the spec is a FILE at `projects/<name>/plans/` written before fan-out, which is now the load-bearing part. Worth a line on the next regeneration. |
| `08-one-operator-many-projects.png` | regenerated for v6 — the old one sold `git clone` per client, which is the model v6 replaced |
| `09-agent-qa.png` | regenerated for v6 (footer: only the protocol file is copied) |
| `og-banner.png` | true |

All nine are capped at 2000 px wide: the set went from ~8.7 MB to ~2.7 MB, which matters because
several of them sit above the fold.

Removed in v6: `01-before-after.png` — the before/after table in the README says the same thing,
and it was the one asset drawn in a different (emoji-face) style. Still in git history.

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
