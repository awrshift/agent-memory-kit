#!/usr/bin/env python3
"""Tests for the landed-commit line of scripts/quiet.sh — run: python3 plugins/memory-kit/scripts/tests/test_quiet_commit.py

The case this suite pins: `git commit` returns 0, no commit exists, and the summary looks clean. A fake `git` on PATH
stands in for that (it answers `commit` with exit 0 and does nothing; every other subcommand goes to the real git).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quiet.sh")
REAL_GIT = shutil.which("git")

FAKE_GIT = f"""#!/usr/bin/env bash
if [ "${{1:-}}" = "commit" ]; then echo "[main 0000000] pretended"; exit 0; fi
exec "{REAL_GIT}" "$@"
"""


class QuietCommit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        os.mkdir(self.repo)
        self.env = dict(os.environ, QUIET_LOG_DIR=os.path.join(self.tmp, "logs"), GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        self.git("init", "-q")
        self.write("a.txt", "one\n")
        self.git("add", "a.txt")
        self.git("commit", "-q", "-m", "first")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        subprocess.run([REAL_GIT, *args], cwd=self.repo, env=self.env, check=True, capture_output=True)

    def write(self, name, text):
        with open(os.path.join(self.repo, name), "w") as fh:
            fh.write(text)

    def quiet(self, *cmd, fake_git=False):
        env = dict(self.env)
        if fake_git:
            bindir = os.path.join(self.tmp, "bin")
            os.makedirs(bindir, exist_ok=True)
            fake = os.path.join(bindir, "git")
            with open(fake, "w") as fh:
                fh.write(FAKE_GIT)
            os.chmod(fake, 0o755)
            env["PATH"] = bindir + os.pathsep + env["PATH"]
        r = subprocess.run(["bash", SCRIPT, *cmd], cwd=self.repo, env=env, capture_output=True, text=True)
        return r.returncode, r.stdout.strip().splitlines()

    def test_real_commit_lands(self):
        self.write("a.txt", "two\n")
        code, out = self.quiet("git", "commit", "-m", "second", "--", "a.txt")
        self.assertEqual(code, 0)
        self.assertTrue(out[-1].startswith("landed: "), out)
        self.assertIn("second", out[-1])

    def test_exit_zero_without_a_commit_is_loud_and_fails(self):
        self.write("a.txt", "two\n")
        code, out = self.quiet("git", "commit", "-m", "second", "--", "a.txt", fake_git=True)
        self.assertEqual(code, 1)
        self.assertTrue(out[-1].startswith("COMMIT NOT LANDED (git exit=0"), out)

    def test_refused_commit_ends_with_the_loud_line(self):
        code, out = self.quiet("git", "commit", "-m", "nothing to commit")
        self.assertNotEqual(code, 0)
        self.assertTrue(out[-1].startswith("COMMIT NOT LANDED (git exit=1"), out)

    def test_other_commands_get_no_commit_line(self):
        for cmd in (("echo", "hi"), ("git", "status"), ("git", "commit", "--dry-run", "-m", "x")):
            _, out = self.quiet(*cmd)
            self.assertFalse(any("landed" in line.lower() for line in out), (cmd, out))


if __name__ == "__main__":
    unittest.main()
