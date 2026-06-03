"""
Lint the knowledge base for structural health.

5 structural checks — all free, no LLM calls needed:
broken links, orphan pages, missing backlinks,
sparse articles, missing frontmatter.

Usage:
    python scripts/lint.py              # run all checks
    python scripts/lint.py --fix        # auto-fix what's possible (missing backlinks)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from config import (
    CONCEPTS_DIR,
    KNOWLEDGE_DIR,
    today_iso,
)


def list_wiki_articles() -> list[Path]:
    if CONCEPTS_DIR.exists():
        return sorted(CONCEPTS_DIR.glob("*.md"))
    return []


def extract_wikilinks(content: str) -> list[str]:
    """Extract all [[wikilinks]] from markdown content."""
    return re.findall(r"\[\[([^\]]+)\]\]", content)


def wiki_article_exists(link: str) -> bool:
    """Check if a wikilinked article exists on disk."""
    path = KNOWLEDGE_DIR / f"{link}.md"
    return path.exists()


def get_word_count(path: Path) -> int:
    """Count words excluding YAML frontmatter."""
    content = path.read_text(encoding="utf-8")
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:]
    return len(content.split())


# ── Checks ────────────────────────────────────────────────────────


def check_broken_links() -> list[dict]:
    """[[wikilinks]] pointing to non-existent articles."""
    issues = []
    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        rel = article.relative_to(KNOWLEDGE_DIR)
        for link in extract_wikilinks(content):
            # Skip daily/ references (external to vault)
            if link.startswith("daily/"):
                continue
            if not wiki_article_exists(link):
                issues.append({
                    "severity": "error",
                    "check": "broken_link",
                    "file": str(rel),
                    "detail": f"Broken link: [[{link}]]",
                })
    return issues


def check_orphan_pages() -> list[dict]:
    """Articles with zero inbound links from other articles."""
    issues = []
    # Build set of all link targets across all articles
    all_targets: dict[str, int] = {}
    for article in list_wiki_articles():
        link_key = str(article.relative_to(KNOWLEDGE_DIR)).replace(".md", "").replace("\\", "/")
        all_targets[link_key] = 0

    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        for link in extract_wikilinks(content):
            if link in all_targets:
                all_targets[link] += 1

    for target, count in all_targets.items():
        if count == 0:
            # Check if referenced in index.md
            index_content = ""
            index_path = KNOWLEDGE_DIR / "index.md"
            if index_path.exists():
                index_content = index_path.read_text(encoding="utf-8")
            if f"[[{target}]]" not in index_content:
                issues.append({
                    "severity": "warning",
                    "check": "orphan_page",
                    "file": f"{target}.md",
                    "detail": f"No articles or index link to [[{target}]]",
                })

    return issues


def check_missing_backlinks() -> list[dict]:
    """A links to B but B doesn't link back to A."""
    issues = []
    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        rel = article.relative_to(KNOWLEDGE_DIR)
        source_link = str(rel).replace(".md", "").replace("\\", "/")

        for link in extract_wikilinks(content):
            if link.startswith("daily/"):
                continue
            target_path = KNOWLEDGE_DIR / f"{link}.md"
            if target_path.exists():
                target_content = target_path.read_text(encoding="utf-8")
                if f"[[{source_link}]]" not in target_content:
                    issues.append({
                        "severity": "suggestion",
                        "check": "missing_backlink",
                        "file": str(rel),
                        "detail": f"[[{source_link}]] → [[{link}]] (no backlink)",
                        "fix": {"target": link, "add_link": source_link},
                    })
    return issues


def check_sparse_articles() -> list[dict]:
    """Articles with fewer than 150 words."""
    issues = []
    for article in list_wiki_articles():
        words = get_word_count(article)
        if words < 150:
            rel = article.relative_to(KNOWLEDGE_DIR)
            issues.append({
                "severity": "suggestion",
                "check": "sparse_article",
                "file": str(rel),
                "detail": f"Sparse: {words} words (recommended: 150+)",
            })
    return issues


def check_missing_frontmatter() -> list[dict]:
    """Articles without YAML frontmatter."""
    issues = []
    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        if not content.startswith("---"):
            rel = article.relative_to(KNOWLEDGE_DIR)
            issues.append({
                "severity": "error",
                "check": "missing_frontmatter",
                "file": str(rel),
                "detail": "Missing YAML frontmatter (---)",
            })
    return issues


# ── Auto-fix ─────────────────────────────────────────────────────


def fix_missing_backlinks(issues: list[dict]) -> int:
    """Add missing backlinks to target articles."""
    fixed = 0
    for issue in issues:
        if issue["check"] != "missing_backlink" or "fix" not in issue:
            continue

        fix = issue["fix"]
        target_path = KNOWLEDGE_DIR / f"{fix['target']}.md"
        if not target_path.exists():
            continue

        content = target_path.read_text(encoding="utf-8")
        source_link = fix["add_link"]

        # Find "## Related Concepts" section and add backlink
        if "## Related Concepts" in content:
            content = content.replace(
                "## Related Concepts\n",
                f"## Related Concepts\n\n- [[{source_link}]]\n",
                1,
            )
            target_path.write_text(content, encoding="utf-8")
            fixed += 1
            print(f"  Fixed: added [[{source_link}]] to {fix['target']}")

    return fixed


# ── Report ───────────────────────────────────────────────────────


def generate_report(all_issues: list[dict]) -> str:
    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]
    suggestions = [i for i in all_issues if i["severity"] == "suggestion"]

    lines = [
        f"# Lint Report — {today_iso()}",
        "",
        f"**Total issues:** {len(all_issues)}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        f"- Suggestions: {len(suggestions)}",
        "",
    ]

    for severity, items, marker in [
        ("Errors", errors, "x"),
        ("Warnings", warnings, "!"),
        ("Suggestions", suggestions, "?"),
    ]:
        if items:
            lines.append(f"## {severity}")
            lines.append("")
            for issue in items:
                lines.append(f"- **[{marker}]** `{issue['file']}` — {issue['detail']}")
            lines.append("")

    if not all_issues:
        lines.append("All checks passed. Knowledge base is healthy.")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Lint the knowledge base")
    parser.add_argument("--fix", action="store_true", help="Auto-fix missing backlinks")
    args = parser.parse_args()

    all_issues: list[dict] = []

    print("Running knowledge base lint checks...\n")

    checks = [
        ("Broken links", check_broken_links),
        ("Orphan pages", check_orphan_pages),
        ("Missing backlinks", check_missing_backlinks),
        ("Sparse articles", check_sparse_articles),
        ("Missing frontmatter", check_missing_frontmatter),
    ]

    for name, check_fn in checks:
        issues = check_fn()
        all_issues.extend(issues)
        status = f"{len(issues)} issue(s)" if issues else "OK"
        print(f"  {name}: {status}")

    # Auto-fix if requested
    if args.fix:
        print("\nAuto-fixing...")
        fixed = fix_missing_backlinks(all_issues)
        print(f"  Fixed {fixed} missing backlinks")

    # Report
    report = generate_report(all_issues)
    print(f"\n{'=' * 50}")
    print(report)

    # Summary
    errors = sum(1 for i in all_issues if i["severity"] == "error")
    if errors > 0:
        print("Errors found — knowledge base needs attention!")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
