# Cursor — verified: skills + AGENTS.md protocol + SessionStart injection

Last verified: 2026-08-31, against `cursor-agent 2026.08.25-3e8eec8` (Cursor CLI, headless
`-p --mode ask` probes), Cursor app 2.1.36 installed but not driven. Auth: logged-in Cursor
account (required for marketplace operations).

## Install (`verified`)

Two paths, both probed:

- **Marketplace by git URL** — no central-marketplace publication needed:
  ```bash
  cursor-agent plugin marketplace add https://github.com/awrshift/agent-memory-kit
  ```
  Result: `✓ Added marketplace memory-kit (1 plugin)` — Cursor's server-side indexer read
  `.claude-plugin/marketplace.json` and resolved the **nested** `plugins/memory-kit` source
  (the plugin description it printed comes from our `plugin.json`). Installing from the
  indexed marketplace into the account is interactive (`/plugins` in a session) —
  `manual-check-needed` for that last click; the CLI prints the tip itself.
- **Local plugin directory** — full load without any marketplace:
  ```bash
  cursor-agent -p --plugin-dir <repo>/plugins/memory-kit "..."
  ```
  Result: **all 8 skills** visible in the session, each reported as `(plugin)`.

## What works (`verified`, canary probes)

- **SessionStart hook injection — the surprise.** With the plugin loaded, a session in an
  adopted repo contained the MEMORY.md canary AND an identity.md-only phrase **without the
  agent opening any file**; without the plugin, the same question answered NO. Cursor CLI
  executes Claude-format `hooks.json` SessionStart and honours `additionalContext` — "wakes up
  already knowing" works on Cursor. (Our hook's env-var fallbacks — cwd for the project,
  `__file__` for the plugin root — are what let it run outside Claude Code.)
- **`AGENTS.md` is auto-loaded and followed** — same probe as Codex: an instruction line in
  `AGENTS.md` was present in context and executed (the agent read `MEMORY.md` and returned its
  canary).
- **`.cursor/skills/` accepts Claude-format skills as-is** — two of our SKILL.md dirs copied
  there unmodified were discovered and listed.

## Not yet probed

- `PreCompact` / `PreToolUse` / `SessionEnd` — whether Cursor executes the other three hook
  events is `manual-check-needed` (PreCompact needs a long session; PreToolUse needs write
  mode). Until probed, treat only injection as guaranteed on Cursor: the compaction block and
  the test guard remain `documented-only` at best.
- Whether an **account-installed** plugin (via interactive `/plugins`) behaves identically to
  `--plugin-dir` — expected, same loader, but `manual-check-needed`.
- The Cursor **GUI app** (`/add-plugin` flow, central-marketplace publication like
  compound-engineering did) — untested; the CLI git-URL path above makes publication optional.

## Central marketplace publication (`documented-only`, 2026-08-31)

Distinct from the verified git-URL path above: a **curated** public listing (searchable
in-app, one-click `/add-plugin memory-kit`). Facts from Cursor's official docs:

- Submission: sign in at `cursor.com/marketplace/publish` and submit the repository link — a
  "plugin publisher application", manually reviewed. Their security page states the policy
  plainly: "We work with a small group of trusted partners… every submission goes through our
  internal review process." No review SLA is published anywhere. Cursor's own
  `cursor/plugin-template` README names a second channel: Slack or `kniparko@anysphere.com`.
- Requirements we satisfy as of v6.3.1: public open-source repo (MIT) · root
  `.cursor-plugin/marketplace.json` (multi-plugin format, `source: plugins/memory-kit` —
  nested paths are officially supported, no restructuring) ·
  `plugins/memory-kit/.cursor-plugin/plugin.json` (kebab-case unique name, description,
  README) · all manifest paths relative · plugin tested locally (the probes above).
- Every update after listing is re-reviewed; unresponsive authors risk delisting.

Status: manifests shipped, application not yet submitted (needs the maintainer's cursor.com
sign-in). Update this section with the outcome and date when it happens.

## Notes

- Cursor CLI also surfaces the user's global skills alongside plugin skills — our probe listed
  ~56 entries including personal ones; namespacing is flat (no `memory-kit:` prefix observed),
  so name collisions with user skills are possible (`observed`, low impact).
- Precedence (per Cursor docs, `documented-only`): Team Rules > Project Rules > User Rules >
  legacy `.cursorrules` > `AGENTS.md`.
