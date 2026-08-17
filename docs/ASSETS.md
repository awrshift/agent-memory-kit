# README assets — state and how they are made

Nine diagrams in `.github/assets/` carry the visual story. They are PNGs, so their text ages with
the product. The rule: **a diagram that states a fact is a fact that has to be swept like any
other** — same discipline as the docs, and a stale panel is a lie in the most-read file.

## State (last swept 2026-08-17, v6.0.0)

| Asset | State |
|---|---|
| `02-daily-workflow.png` | regenerated for v6 (injection carries the hot cache; the ~50-message auto-save prompt is gone) |
| `03-memory-layers.png` | regenerated for v6 (hot cache marked *injected every session*; namespaced skill) |
| `04-promotion-pipeline.png` | true |
| `05-multi-project.png` | regenerated for v6 (plugin identity replaces `CLAUDE.md` in the always-loaded column) |
| `06-hooks-and-operators.png` | regenerated for v6 — four hooks, ten namespaced skills, no `.kit/advanced` panel |
| `07-agent-orchestration.png` | regenerated for v6 (footer: ships inside the plugin) |
| `08-one-operator-many-clones.png` | true |
| `09-agent-qa-loop.png` | regenerated for v6 (footer: only the protocol file is copied) |
| `og-banner.png` | true |

All nine are capped at 2000 px wide: the set went from ~8.7 MB to ~2.7 MB, which matters because
several of them sit above the fold.

Removed in v6: `01-before-after.png` — the before/after table in the README says the same thing,
and it was the one asset drawn in a different (emoji-face) style. Still in git history.

## How to regenerate one

Generated with Google's image models via the REST API — `gemini-3-pro-image` (Nano Banana Pro)
is the one to use for these: the panels are text-dense and the Pro model is the one that renders
long strings without drifting. Pass the CURRENT asset as a style reference so the new panel
matches the set, and give the prompt the **complete text spec**, every string verbatim.

```bash
# GOOGLE_API_KEY from your environment; model default is gemini-3-pro-image
python3 tools/genimg.py .github/assets/06-hooks-and-operators.png prompt.txt out.png
sips -Z 2000 out.png          # keep the set under control
```

Two lessons from doing this, both cheap to repeat and expensive to skip:

1. **"Reproduce this exactly, change only the footer" produces typos.** That prompt shape drifted
   `merges`→`marges`, `silent`→`siient`, `401/403/404`→`401/409/404`, `pollable`→`poliable`.
   Rewriting the same request as a full content spec — every string listed, plus an explicit
   spelling-check list of the words that had drifted — came back clean on the first try.
2. **Read the generated image before committing it.** Every one of those typos was invisible in
   the file size and the API response, and obvious in two seconds of looking.

The prompt files used for the v6 batch are not kept — the spec they encode is this file's state
table plus the copy already visible in each asset.

## Style notes

- The Mermaid diagram in the README ("Where memory lives") can never go stale — it renders from
  text. Prefer Mermaid for structure, PNGs for the pitch.
