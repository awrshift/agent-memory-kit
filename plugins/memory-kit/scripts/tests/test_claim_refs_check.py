#!/usr/bin/env python3
"""Tests for scripts/claim-refs-check.py — run: python3 plugins/memory-kit/scripts/tests/test_claim_refs_check.py

A throwaway git repo with two commits; each case writes a short text and runs the script on it. What this pins: a
named path or commit that does not exist fails the check and is named; one that exists passes. The false-positive
cases covered (never flagged): a URL with a path and a hex segment, a URL's query values (a path, a hash), an
e-mail host, a host name without a scheme, version strings (`v8.2.0`, `release/v1.2.3`), a UUID, a sha256 checksum,
a `#colour`, an `@scope/package`, a glob, a placeholder, a command in backticks and a bare `word/word.js` whose
first segment is no top-level entry of the repo. Also pinned: a path joined to a URL by `|`, `,` or `)` is still
checked, the link pattern's bound (read through `hooks/tests/regex_bounds.py`, CPython's private regex parser; that
test skips, with the reason, on a Python without it) and the default repository (`$CLAUDE_PROJECT_DIR`, else the
current directory) when no `--repo` is given. The short-hash case builds its hash from the shortest prefix of 7+
characters that holds a letter and a digit, so it does not depend on the commit's clock.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import importlib.util
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "claim-refs-check.py")
_spec = importlib.util.spec_from_file_location("claim_refs_check", SCRIPT)
crc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(crc)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "hooks", "tests"))
import regex_bounds  # noqa: E402  the walker shared with hooks/tests
UNKNOWN = "0badc0de1"


class ClaimRefs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        os.mkdir(self.repo)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        self.env.pop("CLAUDE_PROJECT_DIR", None)
        self.git("init", "-q")
        self.write("docs/guide.md", "one\n")
        self.write("src/app.py", "print(1)\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "first")
        self.first = self.git("rev-parse", "HEAD")
        self.write("docs/later.md", "two\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "second")
        self.assertNotEqual(subprocess.run(["git", "cat-file", "-e", UNKNOWN + "^{commit}"], cwd=self.repo,
                                           env=self.env, capture_output=True).returncode, 0)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        r = subprocess.run(["git", *args], cwd=self.repo, env=self.env, check=True, capture_output=True, text=True)
        return r.stdout.strip()

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def check(self, text, *extra):
        body = os.path.join(self.tmp, "body.md")
        with open(body, "w", encoding="utf-8") as fh:
            fh.write(text)
        r = subprocess.run([sys.executable, SCRIPT, body, "--repo", self.repo, *extra], env=self.env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout

    def test_existing_path_passes(self):
        code, out = self.check("Changed `docs/guide.md` and `src/app.py:1` (see [the guide](docs/guide.md#top)).\n")
        self.assertEqual(code, 0, out)
        self.assertIn("2 paths", out)

    def test_missing_path_fails_and_is_named(self):
        code, out = self.check("The rule lives in `docs/missing.md`; the guide is `docs/guide.md`.\n")
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING path  docs/missing.md", out)
        self.assertNotIn("guide.md", out.split("\n", 1)[1])

    def test_missing_link_target_and_bare_path_fail(self):
        code, out = self.check("See [notes](docs/gone.md) and docs/also-gone.md, then ./src/none.py.\n")
        self.assertEqual(code, 1, out)
        for name in ("docs/gone.md", "docs/also-gone.md", "./src/none.py"):
            self.assertIn("MISSING path  " + name, out)

    def test_existing_short_hash_passes(self):
        """The script's hash shape holds a letter and a digit: a 7-char prefix of digits only (about 1 commit in 27)
        is no hash to it, so the prefix is lengthened until it holds both — deterministic whatever the clock."""
        n = next((n for n in range(7, 41) if re.search(r"[a-f]", self.first[:n]) and re.search(r"\d", self.first[:n])),
                 40)
        short = self.first[:n]
        code, out = self.check(f"Landed in {short}; full range `{short}..HEAD`.\n")
        self.assertEqual(code, 0, out)
        self.assertIn("1 hashes", out)

    def test_unknown_hash_fails(self):
        code, out = self.check(f"Fixed in {UNKNOWN} after {self.first[:9]}..{UNKNOWN[:8]}.\n")
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING hash  " + UNKNOWN, out)
        self.assertIn("MISSING hash  " + UNKNOWN[:8], out)
        self.assertNotIn(self.first[:9], out.split("\n", 1)[1])

    def test_path_at_a_ref(self):
        """`--ref`: a file only in the working tree is missing at the ref; a file deleted from the tree is found."""
        self.write("docs/draft.md", "untracked\n")
        os.remove(os.path.join(self.repo, "docs", "later.md"))
        code, out = self.check("`docs/draft.md` and `docs/later.md`\n", "--ref", "HEAD")
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING path  docs/draft.md", out)
        self.assertNotIn("later.md", out.split("\n", 1)[1])
        code, out = self.check("`docs/draft.md`\n")
        self.assertEqual(code, 0, out)

    def test_look_alikes_are_not_flagged(self):
        text = "\n".join([
            "Upstream: https://example.com/org/repo/commit/0badc0de1/docs/none.md and `https://example.com/x/y.md`.",
            "Host without a scheme: `example.com/a.html`; package `@types/node`; flag `--out=dir/x.md`.",
            "Versions: `v8.2.0`, release/v1.2.3, `release/v1.2.3`, 2.0.0-rc.1.",
            "UUID 1a2b3c4d-abcd-4ef0-9a1b-0123456789ab · colour #a1b2c3 · sha256 "
            "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08.",
            "Globs and placeholders: `docs/*.md`, `<dir>/x.md`, `docs/{a,b}.md`, `…/spec.md`.",
            "A command: `git diff --stat main..HEAD -- docs/none.md`. Prose: React/Next.js and and/or, TCP/IP.",
        ])
        code, out = self.check(text + "\n")
        self.assertEqual(code, 0, out)
        self.assertIn("0 paths", out)
        self.assertIn("0 hashes", out)

    def test_url_query_values_and_mail_hosts_are_not_flagged(self):
        """A URL's query value (a path, a hash) and an e-mail host: blanked before the bare-path and hash passes."""
        for text in ("Search: https://example.com/search?path=docs/missing.md here.",
                     "Pinned: https://example.com/x?sha=abc1234f here.",
                     "Write to user@deadbee1.com today."):
            with self.subTest(text=text):
                code, out = self.check(text + "\n")
                self.assertEqual(code, 0, out)
                self.assertIn("0 paths", out)
                self.assertIn("0 hashes", out)

    def test_a_path_joined_to_a_url_is_still_checked(self):
        """The URL span ends at `|`, `,` and `)` as well as at a space: a path written right after one is checked."""
        for text in ("|https://example.com/a|docs/missing.md|", "https://example.com/a,docs/missing.md",
                     "(https://example.com/a)docs/missing.md"):
            with self.subTest(text=text):
                code, out = self.check(text + "\n")
                self.assertEqual(code, 1, out)
                self.assertIn("1 paths", out)
                self.assertIn("MISSING path  docs/missing.md", out)

    @unittest.skipIf(regex_bounds.PARSER is None, regex_bounds.SKIP_REASON)
    def test_a_long_unclosed_link_is_bounded(self):
        """`](` with no `)` was quadratic: the target is at most 200 characters, so each `](` costs a bounded scan."""
        self.assertEqual(regex_bounds.repeats(crc.LINK_RE), [(1, 200)])

    def test_a_link_after_a_long_unclosed_run_is_found(self):
        paths, _, _ = crc.candidates("[x](" * 2000 + " [y](docs/guide.md) [z](" + "a" * 201 + ".md)", {"docs"})
        self.assertEqual(paths, {"docs/guide.md"})  # the real link after the run is still found; 201 chars is not

    def test_default_repository_without_repo(self):
        """No `--repo`: `$CLAUDE_PROJECT_DIR`, else the current directory; `../` resolves from that root."""
        body = os.path.join(self.tmp, "body.md")
        with open(body, "w", encoding="utf-8") as fh:
            fh.write("`docs/guide.md`, `docs/missing.md` and [up](../repo/src/app.py)\n")
        elsewhere = os.path.join(self.tmp, "elsewhere")
        os.mkdir(elsewhere)
        for label, cwd, env in (("cwd", self.repo, self.env),
                                ("CLAUDE_PROJECT_DIR", elsewhere, dict(self.env, CLAUDE_PROJECT_DIR=self.repo))):
            with self.subTest(source=label):
                r = subprocess.run([sys.executable, SCRIPT, body], cwd=cwd, env=env, capture_output=True, text=True)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("3 paths", r.stdout)
                self.assertIn("MISSING path  docs/missing.md", r.stdout)
                self.assertNotIn("guide.md", r.stdout.split("\n", 1)[1])
                self.assertNotIn("app.py", r.stdout.split("\n", 1)[1])

    def test_verbose_lists_found_and_skipped(self):
        code, out = self.check("`docs/guide.md` and React/Next.js\n", "--verbose")
        self.assertEqual(code, 0, out)
        self.assertIn("found   path  docs/guide.md", out)
        self.assertIn("skipped React/Next.js", out)

    def test_stdin_and_usage(self):
        r = subprocess.run([sys.executable, SCRIPT, "-", "--repo", self.repo], input="`docs/none.md`\n",
                           env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("MISSING path  docs/none.md", r.stdout)
        code, _ = self.check("x\n", "--ref", "no-such-ref")
        self.assertEqual(code, 2)
        r = subprocess.run([sys.executable, SCRIPT, os.path.join(self.tmp, "absent.md"), "--repo", self.repo],
                           env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
