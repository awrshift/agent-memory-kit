# Open decisions — the board

Decisions that need the maintainer, not the agent. One row each: the question, what hangs on it,
the recommendation, and the cheapest way to be wrong. Settled ones move to `CHANGELOG.md` and
leave this board.

## Release

| # | Question | Recommendation | Cost of being wrong |
|---|---|---|---|
| D1 | ~~Cut a GitHub release for the version badge?~~ | **Done 2026-08-31** — `v6.4.0` released (the rebrand release, with the multi-host story in the notes); the badge now reads a current number. Releases accompany notable versions from here on. | — |
| D2 | Submit to the community marketplace (`anthropics/claude-plugins-community`)? | **Yes, after one week of self-use on the v6 layout.** Submission pins a commit SHA and CI follows the repo, so a rough week is visible forever. Run `claude plugin validate --strict` first (passes today). | Medium — a public listing is a public first impression. |
| D10 | ~~Tag every version, or only "notable" ones?~~ | **Settled 2026-09-02** — every version gets a tag and a release from 6.5.1 on; the four that shipped untagged (6.3.0, 6.3.1, 6.4.1, 6.5.0) got retroactive annotated tags the same day, releases only from 6.5.1 forward. | — |
| D3 | ~~Keep the repo name `claude-memory-kit`?~~ | **Superseded 2026-08-31** — renamed to `agent-memory-kit`: the kit is verifiably multi-host now (Codex, Cursor), and the old name undersold exactly that. Done before the Cursor marketplace submission so no external catalog carries the old slug. GitHub redirects preserve every existing link; the plugin id `memory-kit@memory-kit` is untouched, so installs don't break. | — |

## Product boundary

| # | Question | Recommendation | Cost of being wrong |
|---|---|---|---|
| D4 | Default answer for the auto-memory question in `/memory-kit:setup` — kit-owns or native-owns? | **Kit-owns, offered as the default but always asked.** The kit's value is that nothing is remembered without a decision; silently deferring to a second writer would undercut it. | Low — one settings line either way. |
| D5 | `system-audit` also lives as a personal global skill outside this repo. Which copy is canonical? | **The plugin copy.** Delete the global one after the plugin is installed, or the two drift and the drift is invisible. | Low, but it grows with time. |
| D6 | Should the orchestration invariants ship as an always-loaded rule by default rather than an offer? | **Keep it an offer.** Always-loaded context is the one thing the kit charges its users for on every single session; making a builder's rule mandatory for a memory-only user contradicts the whole cost model. | Low. |
| D11 | The `qa` agent declares `tools: "*"` while its mandate is observe-only — the only agent whose safety rail is purely instructional. Pin a tool list? | **Not yet.** The lens needs whichever Playwright MCP servers the project's `.mcp.json` names, and their tool ids are project-specific — a pinned list would silently disable the agent in exactly the repos that use it. Revisit when Claude Code's agent frontmatter accepts an MCP-server glob; until then the protocol's two-account rule is the guard. | Medium in a repo with a real account in the QA env — which the protocol template forbids for mutation anyway. |
| D13 | Claude Cowork loads the kit's skills but runs no plugin hooks (`specs/cowork.md`), and it is the app the kit's primary persona is most likely to hold. Ship a Cowork path — `/memory-kit:setup` detecting "no hook ran" and offering the protocol block into `CLAUDE.md` — or wait for Anthropic (issue #47993)? | **Offer the `CLAUDE.md` block now, probe Cowork once with a seat.** One paragraph in setup, no new layer; the T2 mechanism already exists for `AGENTS.md`. Do not build a Cowork-specific runtime. | Medium — a Cowork user who installs from the community marketplace and gets silence is a lost first impression. |
| D12 | Nothing measures whether `/memory-kit:close-session` actually runs. The ritual is where the kit's value lives, and the only telemetry is a SessionEnd timestamp. Count sessions opened vs closed and show the ratio in the session stats? | **Yes, as a hook-side counter, no LLM involved** — SessionStart already bumps `session_count`; `close-session` can touch a `last_close` marker and the stats line can read "12 sessions, 4 closed". Cheap, honest, and the first number a solo operator can act on. | Low — one more line in the stats block. |

## Marketing

| # | Question | Recommendation | Cost of being wrong |
|---|---|---|---|
| D7 | ~~README is ~2.7k words against a ~800–1500 median for developer tools. Trim, or keep the story?~~ | **Settled 2026-09-02** — the operator rewrite landed at ~1,470 words including the collapsed blocks (install for other hosts, builders' layer, file layout), so the visible page is inside the median. The origin story stayed, shortened to what git can prove. | — |
| D8 | The strongest claim available is unused: *"the kit's own memory was never actually loaded for a year, and the fix is measurable."* Lead with it? | **Use it in the release notes and a launch post, not in the README hero.** It is credibility for practitioners and confusion for newcomers who never ran v5. | Low. |
| D9 | ~~Regenerate the stale diagrams~~ | **Done** — six regenerated with `gemini-3-pro-image`, set re-compressed from ~8.7 MB to ~3.0 MB. the old `01-before-after.png` was dropped rather than redrawn — the table under it already carried the point (the current `01-system-map.png` is a later, unrelated asset). | — |

## Recently settled

- Multi-platform (v6.3.0, 2026-08-31): the **tier model** — T1 hook enforcement on Claude Code,
  T2 `AGENTS.md` protocol elsewhere, T3 plain files. Canonical source stays the Claude Code
  plugin format in the **nested** layout: Codex and Cursor both verifiably read it natively
  (skills visible, nested marketplace source resolves; Cursor CLI even runs the SessionStart
  hook). A converter pipeline and a root-native layout migration
  were deliberately NOT adopted — either waits until a real host demands it. Per-host truth
  lives in `docs/specs/`.
- One plugin instead of three (v6.0.0) — skill bodies load on invoke, so the split bought nothing.
- `/close-day` and the daily chronicle: retired, not re-parked in an opt-in folder.
- `periodic-save.sh`: removed rather than optimised — PreCompact already covers the moment that matters.
- Diagrams: regenerated in-house rather than captioned-as-stale (D9). `tools/genimg.py` + the
  lessons in [ASSETS.md](ASSETS.md) make the next sweep cheap.
- CI: `tools/check-repo.py` + `.github/workflows/checks.yml` — manifests, hook profiles, the
  no-scaffolding guarantee and every link now fail the build instead of a reader's trust.
