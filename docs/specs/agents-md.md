# The AGENTS.md convention — the Tier 2 delivery mechanism

Last verified: 2026-08-31 (Codex probe only; everything else `documented-only`).

`AGENTS.md` at a repository root is the emerging cross-vendor convention for "instructions
every agent host auto-loads". It is what makes Tier 2 possible at all: a host that executes no
hooks can still be *told*, in a file it always reads, to go read the memory files itself.
`/memory-kit:setup` offers to append the kit's protocol block
(`templates/workspace/AGENTS-MEMORY-PROTOCOL.md`) to this file.

## Who auto-loads it

| Host | Status | Evidence |
|---|---|---|
| Codex CLI | **verified 2026-08-31** | canary in `AGENTS.md` was in session context and its instruction was executed (see `codex.md`) |
| Cursor | **verified 2026-08-31** | same canary probe as Codex, via `cursor-agent -p`: the `AGENTS.md` instruction was in context and executed (see `cursor.md`) |
| GitHub Copilot CLI | **verified 2026-08-31** | same canary probe via `copilot -p`: instruction in context, executed, MEMORY.md canary returned (see `copilot.md`) |
| Claude Code | **does not need it** | the kit's SessionStart hook injects the same content (`context/identity.md`); scaffolding the block is still harmless — CC reads `CLAUDE.md`, not `AGENTS.md` |

The compound-engineering-plugin repo treats one shared `AGENTS.md` as canonical and ships
`CLAUDE.md` as a filesystem symlink to it — the same "one file, many host conventions" move,
worth stealing if a host ever demands a differently-named twin.

## Drift rules for the protocol block

- The block is fenced by `<!-- memory-kit protocol vX.Y.Z -->` … `<!-- /memory-kit protocol -->`.
  An upgrade REPLACES the marked block; it never appends a second copy.
- The block stays **under ~2 KB** — it is always-loaded context in every foreign host, so it
  obeys the same cost discipline as `.claude/rules/`.
- The block must never contradict `context/identity.md`; identity.md is the SSOT the block is
  distilled from. A change to one in a commit touches the other in the same commit.
