---
description: Ask the knowledge base a natural-language question
---

# /memory-query

Query the knowledge base using index-guided retrieval. The LLM reads `knowledge/index.md`, picks 3-7 relevant articles, reads them, and synthesizes an answer with `[[wikilink]]` citations.

No RAG, no embeddings — works at personal scale (50-500 articles) per Karpathy's observation that a structured index outperforms cosine similarity when the LLM can reason over it.

## Usage

```
/memory-query How does the compile pipeline work?
/memory-query What patterns do I use for Neo4j?
/memory-query What decisions did we make about pricing?
```

## When to use

- You know the knowledge base has information but don't remember the exact path
- You want a synthesis across multiple articles
- You want citations back to sources

## Execution

!python3 .claude/memory/scripts/query.py "$ARGUMENTS"
