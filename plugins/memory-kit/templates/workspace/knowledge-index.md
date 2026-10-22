# Knowledge — Topical reference index

`knowledge/concepts/` is the **facts + rationale** layer. Topic-oriented articles that explain *what* and *why*.

**Agent writes these.** The agent distils articles from the date-tagged patterns in `.claude/memory/MEMORY.md` during `/memory-kit:close-session` once enough observations accumulate around a single topic.

---

## When an article gets written here

- A topic has been touched on 3+ distinct dates in `MEMORY.md` with accumulating detail
- The facts are stable (not changing session-to-session)
- A future-you would benefit from reading the rationale instead of re-deriving it

**Not** for:
- Short cross-session patterns → `.claude/memory/MEMORY.md`
- Mechanical constraints → `.claude/rules/*.md`
- Per-project tasks, specs, research, decisions, QA → `projects/<name>/` (its `README.md` is the map)

---

## Article frontmatter

Every article in `concepts/` starts with:

```yaml
---
title: <topic>
status: current | frozen | superseded | historical | archived   # one vocabulary: reference/doc-governance.md
created: YYYY-MM-DD
updated: YYYY-MM-DD
compiled-from: [2026-04-20, 2026-04-22, ...]   # dates of the MEMORY.md entries this distils
tags: [tag1, tag2]
---
```

A new fact goes INTO the body of its topic section with a short date tag (`[since YYYY-MM-DD]`), and bump `updated`. The line it replaces moves to the article's final `## History` section. Never append dated blocks at the end of an article: an article is the current truth on its topic, the history sits below it, and git keeps the rest.

---

## Index

<!-- Agent maintains this list during /close-session. One line per concept. -->

(empty — `/memory-kit:close-session` will populate when enough MEMORY observations accumulate)

---

## Differences from adjacent layers

| Layer | Answers | Scope | Example entry |
|---|---|---|---|
| `knowledge/concepts/` | «what is X, why is it the way it is» | Facts + rationale | «our typography scale: 43 paired sub-tokens, reasoning per level» |
| `.claude/memory/MEMORY.md` | «short patterns noticed recently» | Date-tagged one-liners | «[2026-04-24] user prefers plain prose in status updates» |
| `.claude/rules/*.md` | «what must always / never happen» | Mechanical constraints | «never push upstream without preflight exit 0» |

Same fact can surface at different layers in its lifecycle: observation in conversation → dated pattern in MEMORY → article in knowledge → enforceable rule. Promotion is agent-driven, always on `/memory-kit:close-session`, always with user verbal confirmation.
