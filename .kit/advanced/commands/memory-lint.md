---
description: Run 5 structural health checks on the knowledge base
---

# /memory-lint

Run 5 structural health checks (all free, no LLM calls):

1. **Broken links** — `[[wikilinks]]` pointing to non-existent articles
2. **Orphan pages** — Articles with zero inbound links
3. **Missing backlinks** — A links to B but B doesn't link back
4. **Sparse articles** — Under 150 words
5. **Missing frontmatter** — Articles without YAML frontmatter

## Flags

- `--fix` — auto-add missing backlinks

## Execution

!python3 .claude/memory/scripts/lint.py $ARGUMENTS

## Related

- `/memory-query` — natural-language search across the knowledge base
- `/memory-usage` — hot/cold file report (what's safe to archive)
