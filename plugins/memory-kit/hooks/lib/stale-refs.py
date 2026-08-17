#!/usr/bin/env python3
"""Stale-reference check for the LIVE memory layer.

The #1 empirical failure of LLM memory systems is *stale beliefs* — memory
keeps asserting facts that have since changed, and that actively hurts vs.
running fresh (see Continual Learning Bench, arXiv 2606.05661).

This is the deterministic "detect" half: scan the TRUSTED,
re-applied-every-session memory docs for file-path references that no longer
resolve to a file (in this repo, a sibling repo, or $HOME). A no-resolve hit is
a candidate for "verify → update → delete" — never auto-deleted (the agent
proposes, the user confirms — the same gate as every memory write).

`tmp/` paths and template placeholders are skipped everywhere.

Free: no LLM calls. Advisory: prints a report, exit 0.
The session-start hook runs this automatically on the always-loaded layer.

Usage:  python3 .claude/memory/scripts/stale-refs.py [extra/path.md ...]
"""

import os
import re
import sys
from pathlib import Path

# v6: this script now ships INSIDE the plugin, so its own location says nothing about the
# repository being checked — deriving the root from __file__ would point at the plugin cache
# and find nothing. The harness supplies the project root.
ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
HOME = Path.home()

# Declared external dependencies your memory legitimately references (e.g. a
# sibling repo your notes point into). A ref resolving under one of these is NOT
# stale. Empty by default — add absolute Paths for your own setup, e.g.:
#     EXTERNAL_ROOTS = [HOME / "dev/my-other-repo"]
# Checked via direct .exists() only (no directory walk — cheap on large repos).
EXTERNAL_ROOTS: list[Path] = []

# Trusted, auto-loaded or memory-curated docs — where a stale ref does real harm.
DEFAULT_TARGETS = [
    "CLAUDE.md",
    ".claude/memory/MEMORY.md",
    *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "knowledge" / "concepts").glob("*.md"))],
    *[str(p.relative_to(ROOT)) for p in sorted((ROOT / ".claude" / "rules").glob("*.md"))],
]

# Longest-first so e.g. `json` wins over `js`; a trailing boundary makes it robust either way.
EXT = (r"tsx|ts|jsonl|json|jsx|mjs|cjs|js|mdx|md|html|yaml|yml|sh|sql|css|txt|py|drawio")
# Left boundary so we never start mid-path; allow only ./ ../ ~/ as a leading prefix (not a bare /,
# which would be a separator stolen from the preceding token).
PATH_RE = re.compile(
    rf"(?<![\w/~.\-])((?:\.\.?/|~/)?[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+\.(?:{EXT}))(?![A-Za-z0-9])"
)
PRUNE = {".git", "node_modules", "dist", "build", "coverage", ".next",
         "tmp", ".venv", "venv", "__pycache__", ".turbo", "out"}


def repo_files(base: Path) -> set[str]:
    """All file relpaths (posix) under base, pruning vendored/build/scratch dirs."""
    found = set()
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        rel = Path(dirpath).relative_to(base)
        for fn in filenames:
            found.add((rel / fn).as_posix().removeprefix("./"))
    return found


def skip(cand: str) -> bool:
    if "://" in cand or cand.startswith("node:") or "*" in cand:
        return True
    if "YYYY" in cand or "<" in cand or ">" in cand:        # template placeholder
        return True
    if "tmp/" in cand:                                       # gitignored scratch
        return True
    if ".." in cand and not cand.startswith(("./", "../")):  # a.md..b.md range
        return True
    head = cand.split("/", 1)[0]                             # domain w/o scheme (github.com/...)
    if "." in head and not head.startswith("."):
        return True
    return False


def resolves(cand: str, doc_dir: Path, repo_set: set[str]) -> bool:
    if cand.startswith(("./", "../")):                       # relative to the doc itself
        return (doc_dir / cand).exists()
    if cand.startswith("~"):
        return Path(cand).expanduser().exists()
    if (ROOT / cand).exists():                              # exact, repo-relative
        return True
    tail = "/" + cand
    if any(rp == cand or rp.endswith(tail) for rp in repo_set):  # nested
        return True
    if (HOME / cand).exists():                             # ~/.claude/…, Desktop/…, etc.
        return True
    if (ROOT.parent / cand).exists():                      # bare sibling repo
        return True
    for ext in EXTERNAL_ROOTS:                             # user-declared external deps
        if (ext / cand).exists():
            return True
    return False


def main() -> int:
    targets = sys.argv[1:] or DEFAULT_TARGETS
    repo_set = repo_files(ROOT)
    total_stale, scanned = 0, 0
    for t in targets:
        path = ROOT / t
        if not path.exists():
            print(f"  ⚠ target missing: {t}")
            continue
        scanned += 1
        hits = set()
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in PATH_RE.findall(line):
                cand = m.strip().rstrip(".,;:)`")
                if skip(cand) or resolves(cand, path.parent, repo_set):
                    continue
                hits.add((i, cand))
        if hits:
            print(f"\n✗ {t}")
            for ln, cand in sorted(hits):
                print(f"    L{ln}: {cand}")
            total_stale += len(hits)
    print(f"\n— scanned {scanned} files, {total_stale} unresolved path reference(s)")
    print("  (advisory — verify each: renamed? moved? deleted? then update/remove the memory entry)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
