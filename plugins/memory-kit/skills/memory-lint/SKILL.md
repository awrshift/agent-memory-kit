---
name: memory-lint
description: Structural health checks on the knowledge base — broken wikilinks, orphan pages, missing backlinks, sparse articles, missing frontmatter. Use when the user says "/memory-kit:memory-lint", "lint the knowledge base", "проверь базу знаний", or when knowledge/concepts/ has grown enough to rot.
allowed-tools: Bash, Read, Edit
model: sonnet
---

# /memory-kit:memory-lint

Run 5 structural health checks (all free, no LLM calls):

1. **Broken links** — `[[wikilinks]]` pointing to non-existent articles
2. **Orphan pages** — Articles with zero inbound links
3. **Missing backlinks** — A links to B but B doesn't link back
4. **Sparse articles** — Under 150 words
5. **Missing frontmatter** — Articles without YAML frontmatter

## Flags

- `--fix` — auto-add missing backlinks

## Execution

!python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint.py" $ARGUMENTS

## Related

- `/memory-kit:memory-usage` — hot/cold file report (what's safe to archive)
