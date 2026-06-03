# Knowledge — Topical reference index

`knowledge/concepts/` is the **facts + rationale** layer. Topic-oriented articles that explain *what* and *why*.

**Agent writes these.** The agent distils articles from `daily/*.md` during `/close-day` once enough observations accumulate around a single topic.

---

## When an article gets written here

- A topic has been touched 5+ times across `daily/*.md` with accumulating detail
- The facts are stable (not changing session-to-session)
- A future-you would benefit from reading the rationale instead of re-deriving it

**Not** for:
- Short cross-session patterns → `.claude/memory/MEMORY.md`
- Mechanical constraints → `.claude/rules/*.md`
- Per-project tasks/materials → `projects/<name>/`

---

## Article frontmatter

Every article in `concepts/` starts with:

```yaml
---
title: <topic>
status: canonical | draft | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
compiled-from: [daily/2026-04-20.md, daily/2026-04-22.md, ...]
tags: [tag1, tag2]
---
```

When you append a new section to an existing article, prefix the section heading with the date — `## [YYYY-MM-DD] New finding from today's research`. This keeps the article's evolution traceable and lets `/close-day` audit see which articles got refreshed recently.

---

## Index

<!-- Agent maintains this list during /close-day. One line per concept. -->

(empty — `/close-day` will populate when enough daily observations accumulate)

---

## Differences from adjacent layers

| Layer | Answers | Scope | Example entry |
|---|---|---|---|
| `knowledge/concepts/` | «what is X, why is it the way it is» | Facts + rationale | «our typography scale: 43 paired sub-tokens, reasoning per level» |
| `.claude/memory/MEMORY.md` | «short patterns noticed recently» | Date-tagged one-liners | «[2026-04-24] user prefers plain prose in status updates» |
| `.claude/rules/*.md` | «what must always / never happen» | Mechanical constraints | «never push upstream without preflight exit 0» |

Same fact can surface at different layers in its lifecycle: observation in daily → pattern in MEMORY → article in knowledge → enforceable rule. Promotion is agent-driven, always on `/close-day`, always with user verbal confirmation.
