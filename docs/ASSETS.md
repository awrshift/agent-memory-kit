# README assets — state and regeneration brief

Nine diagrams in `.github/assets/` carry the visual story. They are PNGs, so their text ages
with the product — this file records which ones are true right now and what a regeneration must
say. The rule: **a diagram that states a fact is a fact that has to be swept like any other**
(same discipline as the docs).

| Asset | State | Action |
|---|---|---|
| `01-before-after.png` | true — no version-specific claims | keep; style refresh optional (see below) |
| `02-daily-workflow.png` | **2 stale lines** | regenerate |
| `03-memory-layers.png` | true (paths unchanged); `/close-session` now namespaced | regenerate at next batch |
| `04-promotion-pipeline.png` | true | keep |
| `05-multi-project.png` | mostly true; "CLAUDE.md — agent identity" is now the plugin's `identity.md` | regenerate at next batch |
| `06-hooks-and-operators.png` | **stale in every panel** | **removed from README**; regenerate before re-embedding |
| `07-agent-orchestration.png` | true except the footer line | regenerate footer |
| `08-one-operator-many-clones.png` | true | keep |
| `09-agent-qa-loop.png` | true except the footer line | regenerate footer |
| `og-banner.png` | true | keep |

## Exact copy for the regenerations

**02 — How a session works.** Step 1 caption becomes: *"hook injects: your hot cache +
`context/handoffs/<newest>.md` — Claude already knows where you left off"*. Delete
"auto-save every ~50 messages" from step 2; replace with "compaction blocked until state is
written". Step 3 label: `/memory-kit:close-session`.

**06 — Hooks & skills.** Subtitle: *"Four silent guards. Ten skills you can type."* Hooks panel:
`session-start.py` — injects the working agreement, your hot cache, the newest handoff, the
knowledge index · `pre-compact.sh` — blocks compaction until memory is saved and inside all
3 caps · `protect-tests.py` — asks before an existing test is edited · `session-end.sh` —
timestamps the close. Skills panel (all `/memory-kit:`): `close-session` · `memory-audit` ·
`system-audit` · `setup` · `tour` · `memory-lint` · `memory-usage` · `session-review` ·
`second-opinion` · `qa-sweep`. Footer: *"One plugin. Skills cost nothing until you invoke them."*
Delete the `.kit/advanced/` panel entirely.

**07 — Agent-orchestrated work.** Replace the last line with: *"Ships inside the plugin —
`/memory-kit:session-review` · `/memory-kit:second-opinion` · executor / recon / idea-validator."*

**09 — Agent QA.** Replace the last line with: *"`/memory-kit:qa-sweep` ships in the plugin;
only the protocol file `docs/qa/README.md` is copied into your repo."*

**03 / 05, when convenient.** In 03, `/close-session` → `/memory-kit:close-session`. In 05,
the "ALWAYS LOADED (shared)" column: replace `CLAUDE.md — agent identity` with
`plugin identity — injected every session`, and mark `MEMORY.md` as *injected by the hook*
rather than auto-loaded (that wording was the bug v6 fixed).

## Style notes (optional, not blocking)

- `01` and `05` are ~2 MB each — the two heaviest files in the repo, both above the fold on slow
  connections. Re-export at the same width with tighter compression.
- `01` uses emoji faces; every other asset uses the clean neon-card system. It reads as a
  different product. Aligning it would make the page feel designed rather than assembled.
- The Mermaid diagram in the README ("Where memory lives") is the one that can never go stale —
  it renders from text. Prefer Mermaid for anything structural, and keep PNGs for the pieces
  where the visual pitch matters.
