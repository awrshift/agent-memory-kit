"""
Query the knowledge base using index-guided retrieval.

Uses `claude -p` (subscription) to read index.md + relevant articles
and synthesize an answer. No RAG, no embeddings — the LLM reads a
structured index and picks what to read in full.

Usage:
    python scripts/query.py "How does Memory Kit work?"
    python scripts/query.py "What patterns do I use for Neo4j?"
"""

from __future__ import annotations

import argparse
import os
import subprocess

from config import (
    CONCEPTS_DIR,
    INDEX_FILE,
    ROOT_DIR,
)


def read_wiki_index() -> str:
    if INDEX_FILE.exists():
        return INDEX_FILE.read_text(encoding="utf-8")
    return "(empty index)"


def build_query_prompt(question: str) -> str:
    """Build the query prompt for claude -p."""
    wiki_index = read_wiki_index()

    return f"""You are a knowledge base query engine. Answer the user's question by consulting
the wiki in `knowledge/` (project root).

## How to Answer

1. Read the INDEX below to find relevant articles (3-7 articles typically)
2. Use Read tool to read those articles from {CONCEPTS_DIR}
3. Synthesize a clear, thorough answer
4. Cite sources using [[wikilinks]] (e.g., [[concepts/neo4j-patterns]])
5. If the knowledge base doesn't contain relevant information, say so honestly

## Knowledge Base Index

{wiki_index}

## Question

{question}
"""


def run_query(question: str) -> bool:
    """Execute the query via claude -p subprocess."""
    prompt = build_query_prompt(question)

    # Strip ANTHROPIC_API_KEY to use subscription
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

    cmd = [
        "claude",
        "-p", prompt,
        "--allowedTools", "Read,Glob,Grep",
        "--permission-mode", "acceptEdits",
        "--output-format", "text",
        "--max-turns", "15",
        "--model", "sonnet",
    ]

    print(f"Question: {question}")
    print("-" * 60)
    print("Querying knowledge base (this may take 20-40s)...\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # stream output directly
            text=True,
            env=env,
            cwd=str(ROOT_DIR),
            timeout=180,
        )

        if result.returncode != 0:
            print(f"\nError: claude -p exited with code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("\nError: query timed out after 3 minutes")
        return False
    except FileNotFoundError:
        print("\nError: 'claude' command not found. Is Claude Code installed?")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Query the personal knowledge base")
    parser.add_argument("question", help="The question to ask")
    args = parser.parse_args()

    success = run_query(args.question)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
