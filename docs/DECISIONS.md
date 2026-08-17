# Open decisions — the board

Decisions that need the maintainer, not the agent. One row each: the question, what hangs on it,
the recommendation, and the cheapest way to be wrong. Settled ones move to `CHANGELOG.md` and
leave this board.

## Release

| # | Question | Recommendation | Cost of being wrong |
|---|---|---|---|
| D1 | Cut `v6.0.0` as a GitHub release, or ship quietly on `main`? | **Cut the release.** The version badge reads from GitHub releases, so it currently shows a v5 number on a v6 README — the first credibility signal a visitor sees is stale. | Low. A release can be re-tagged. |
| D2 | Submit to the community marketplace (`anthropics/claude-plugins-community`)? | **Yes, after one week of self-use on the v6 layout.** Submission pins a commit SHA and CI follows the repo, so a rough week is visible forever. Run `claude plugin validate --strict` first (passes today). | Medium — a public listing is a public first impression. |
| D3 | Keep the repo name `claude-memory-kit` now that it also carries the builder's layers? | **Keep it.** The name is the story and the install line reads `memory-kit@memory-kit`. Renaming breaks every existing link for a marginal gain in scope accuracy. | High to reverse. |

## Product boundary

| # | Question | Recommendation | Cost of being wrong |
|---|---|---|---|
| D4 | Default answer for the auto-memory question in `/memory-kit:setup` — kit-owns or native-owns? | **Kit-owns, offered as the default but always asked.** The kit's value is that nothing is remembered without a decision; silently deferring to a second writer would undercut it. | Low — one settings line either way. |
| D5 | `system-audit` also lives as a personal global skill outside this repo. Which copy is canonical? | **The plugin copy.** Delete the global one after the plugin is installed, or the two drift and the drift is invisible. | Low, but it grows with time. |
| D6 | Should the orchestration invariants ship as an always-loaded rule by default rather than an offer? | **Keep it an offer.** Always-loaded context is the one thing the kit charges its users for on every single session; making a builder's rule mandatory for a memory-only user contradicts the whole cost model. | Low. |

## Marketing

| # | Question | Recommendation | Cost of being wrong |
|---|---|---|---|
| D7 | README is ~2.7k words against a ~800–1500 median for developer tools. Trim, or keep the story? | **Keep the narrative but move the proof up:** install is now above the fold, and the FAQ answers the "vs built-in memory" question early. If a trim happens, cut the "Before / after" table (the graphic already says it) before cutting the origin story — the story is the differentiator. | Low, reversible. |
| D8 | The strongest claim available is unused: *"the kit's own memory was never actually loaded for a year, and the fix is measurable."* Lead with it? | **Use it in the release notes and a launch post, not in the README hero.** It is credibility for practitioners and confusion for newcomers who never ran v5. | Low. |
| D9 | Regenerate the four stale diagrams now, or drop to Mermaid-first? | **Regenerate 06 first** (it is the only one pulled from the README), then 02/07/09 footers. Keep PNGs for the pitch, Mermaid for structure — copy is in [ASSETS.md](ASSETS.md). | Low, but a wrong diagram is a load-bearing lie in the most-read file. |

## Recently settled

- One plugin instead of three (v6.0.0) — skill bodies load on invoke, so the split bought nothing.
- `/close-day` and the daily chronicle: retired, not re-parked in an opt-in folder.
- `periodic-save.sh`: removed rather than optimised — PreCompact already covers the moment that matters.
