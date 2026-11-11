#!/usr/bin/env python3
"""Every path and commit an outgoing text names must exist — run before a PR body, a release note or a message leaves.

    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claim-refs-check.py" <text.md | -> [--repo DIR ...] [--ref REF] [--verbose]

A claim told before its check («written into the spec» before the line was written, a commit named that does not
exist yet) reads exactly like a true one. This check is mechanical and narrow: it proves the NAMED THINGS exist,
never that the sentence about them is true.

Reads the text file (`-` = stdin). Repositories: every `--repo` (repeatable), else `$CLAUDE_PROJECT_DIR`, else the
current directory. A reference is found when it exists in ANY of them. A relative path (`docs/x.md`, `./x`, `../x`, a
link target) resolves from each repository's root, never from the folder the text file sits in.

Shapes it sees:
  path   a token inside backticks or a relative markdown link target `[x](a/b.md)` that holds a `/` and ends in
         `/` or in a file extension that starts with a letter (`.md`, `.py`, not `.0`); a bare token in prose of
         the same shape only when it starts with `./` or `../` or its first segment is a top-level entry of a
         repository (`docs/x.md` when `docs/` exists). A trailing `:12` / `:12-20` / `#anchor` is cut. Found =
         it exists in the working tree, or — with `--ref REF` — in that ref's tree (`git cat-file -e REF:path`).
         Absolute and `~/` paths are checked as given.
  hash   7–40 lowercase hex characters with at least one letter and one digit, standing alone (not inside a
         word, a path, a URL, a `#colour`, a UUID or a longer hex string; both ends of `a..b` count). Found =
         `git cat-file -e <hash>^{commit}` succeeds.
Skipped by shape (never flagged): URLs (`scheme://…`, `mailto:`) and e-mail addresses — blanked, query values and
host names included, before the bare-path and hash passes — a token whose first segment is a host name
(`example.com/a.html`) unless a repository has that entry, `@scope/name`, globs and placeholders (`*`, `<…>`,
`{…}`, `…`, `...`), a token with a space or starting with `-`, version strings (`release/v1.2.3` — the extension
starts with a digit), hex runs over 40 characters (checksums). `--verbose` also prints every reference found and
every path-like token skipped, with the reason.

What it cannot see: a claim in prose («the test covers X», «nothing else changed», a number) — only that a named
thing exists; a path written without a `/` (`README.md`) or a bare path under a directory that exists nowhere; a
link target over 200 characters; a hash under 7 characters, in upper case or inside a URL; whether a hash is on the
branch the text is about (only that git knows it). An ambiguous short hash (two objects share the prefix) counts as
missing — lengthen it.

Exit 0 = every reference found · 1 = the missing ones are listed (fix the text or create the thing first) · 2 = usage.
Tests: scripts/tests/test_claim_refs_check.py. Python 3.9+, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

TICK_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\]\(([^)\s]{1,200})\)")  # bounded: a run of `](` with no `)` was quadratic
# URL and e-mail spans, blanked before the bare-path and hash passes; a match starts only where a run starts
URL_RE = re.compile(r"(?<![A-Za-z0-9+.-])[A-Za-z][A-Za-z0-9+.-]{0,31}://\S*")
EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]{1,64}@[\w.-]{1,255}")
BARE_RE = re.compile(r"(?<![\w/.:@~-])((?:\.\.?/)?[\w.-]+(?:/[\w.-]+)+/?)")
HASH_RE = re.compile(r"(?:(?<=\.\.)|(?<![0-9A-Za-z_/#.-]))([0-9a-f]{7,40})(?![0-9A-Za-z_-])")
SUFFIX_RE = re.compile(r"(?::\d+(?:-\d+)?|#[\w.-]*)$")
EXT_RE = re.compile(r"\.[A-Za-z][A-Za-z0-9]{0,7}$")
HOST_RE = re.compile(r"^[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def skip_reason(tok: str, top_level: set[str]) -> str | None:
    """Why a token is not a path to check; None when it has the path shape."""
    if SCHEME_RE.match(tok):
        return "url"
    if tok.startswith(("-", "@")):
        return "flag or package"
    if any(c in tok for c in "<>*{}[] ?|") or "\u2026" in tok or "..." in tok:
        return "placeholder, glob or command"
    if "/" not in tok:
        return "no slash"
    first = tok.split("/", 1)[0]
    if HOST_RE.match(first) and first not in top_level:
        return "host"
    if not (tok.endswith("/") or EXT_RE.search(tok)):
        return "no extension"
    return None


def blank_web(text: str) -> str:
    """The text with every URL and e-mail span replaced by a space: never a path or a commit of a repository."""
    return EMAIL_RE.sub(" ", URL_RE.sub(" ", text))


def candidates(text: str, top_level: set[str]) -> tuple[set[str], set[str], list[tuple[str, str]]]:
    """(paths, hashes, skipped path-like tokens with the reason)."""
    paths: set[str] = set()
    skipped: list[tuple[str, str]] = []
    marked = [m.group(1) for m in TICK_RE.finditer(text)] + [m.group(1) for m in LINK_RE.finditer(text)]
    for raw in marked:
        tok = SUFFIX_RE.sub("", raw.strip())
        reason = skip_reason(tok, top_level)
        if reason is None:
            paths.add(tok)
        elif "/" in tok:
            skipped.append((tok, reason))
    prose = blank_web(TICK_RE.sub(" ", text))
    for m in BARE_RE.finditer(prose):
        tok = SUFFIX_RE.sub("", m.group(1).rstrip(".,;:"))
        if tok in paths or skip_reason(tok, top_level) is not None:
            continue
        if tok.startswith(("./", "../")) or tok.split("/", 1)[0] in top_level:
            paths.add(tok)
        else:
            skipped.append((tok, "bare, first segment is no top-level entry"))
    hashes = {h for h in HASH_RE.findall(blank_web(text)) if re.search(r"[a-f]", h) and re.search(r"\d", h)}
    return paths, hashes, skipped


def git_ok(repo: str, *args: str) -> bool:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True).returncode == 0


def top_entries(repo: str, ref: str | None) -> set[str]:
    if ref:
        out = subprocess.run(["git", "-C", repo, "ls-tree", "--name-only", ref], capture_output=True, text=True)
        return set(out.stdout.split("\n")) - {""} if out.returncode == 0 else set()
    try:
        return set(os.listdir(repo))
    except OSError:
        return set()


def path_found(path: str, repos: list[str], ref: str | None) -> bool:
    expanded = os.path.expanduser(path)
    if os.path.isabs(expanded):
        return os.path.exists(expanded)
    if ref:
        rel = os.path.normpath(expanded)
        return any(git_ok(r, "cat-file", "-e", f"{ref}:{rel}") for r in repos)
    return any(os.path.exists(os.path.join(r, expanded)) for r in repos)


def hash_found(sha: str, repos: list[str]) -> bool:
    return any(git_ok(r, "cat-file", "-e", f"{sha}^{{commit}}") for r in repos)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Every path and commit hash a text names must exist.")
    ap.add_argument("text", help="the text file to check; - reads stdin")
    ap.add_argument("--repo", action="append", default=[], help="a repository to resolve in (repeatable)")
    ap.add_argument("--ref", help="check paths in this ref's tree instead of the working tree")
    ap.add_argument("--verbose", action="store_true", help="also list found references and skipped tokens")
    args = ap.parse_args(argv)
    if args.text == "-":
        text, name = sys.stdin.read(), "<stdin>"
    elif os.path.isfile(args.text):
        with open(args.text, encoding="utf-8", errors="replace") as fh:
            text, name = fh.read(), args.text
    else:
        print(f"no such file: {args.text}", file=sys.stderr)
        return 2
    repos = [os.path.abspath(r) for r in args.repo] or [os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()]
    for repo in repos:
        if not git_ok(repo, "rev-parse", "--git-dir"):
            print(f"not a git repository: {repo}", file=sys.stderr)
            return 2
    if args.ref and not any(git_ok(r, "rev-parse", "--verify", "-q", args.ref) for r in repos):
        print(f"unknown ref: {args.ref}", file=sys.stderr)
        return 2
    top: set[str] = set()
    for repo in repos:
        top |= top_entries(repo, args.ref)
    paths, hashes, skipped = candidates(text, top - {".git"})
    missing = [("path", p) for p in sorted(paths) if not path_found(p, repos, args.ref)]
    missing += [("hash", h) for h in sorted(hashes) if not hash_found(h, repos)]
    where = f" at {args.ref}" if args.ref else ""
    print(f"{name}: {len(paths)} paths{where}, {len(hashes)} hashes checked; {len(missing)} not found")
    for kind, ref in missing:
        print(f"  MISSING {kind}  {ref}")
    if args.verbose:
        gone = set(missing)
        for kind, ref in [("path", p) for p in sorted(paths)] + [("hash", h) for h in sorted(hashes)]:
            if (kind, ref) not in gone:
                print(f"  found   {kind}  {ref}")
        for tok, reason in sorted(set(skipped)):
            print(f"  skipped {tok}  ({reason})")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
