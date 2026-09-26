#!/usr/bin/env python3
"""Tests for the 7.1 rails nudge in hooks/session-start.py — run:
python3 plugins/memory-kit/hooks/tests/test_session_start_rails.py

Each case builds a throwaway repo and a throwaway HOME (so the user's real ~/.claude/settings.json
never leaks in), runs the SessionStart wiring from hooks.json for every source, and reads the
injected context — the only proof of what the agent sees.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as _fh:
    WIRING = json.load(_fh)["hooks"]["SessionStart"][0]["hooks"][0]["command"]
SOURCES = ("startup", "clear", "fork", "resume", "compact")


class RailsNudge(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="cmk-rails-repo-")
        self.home = tempfile.mkdtemp(prefix="cmk-rails-home-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        os.makedirs(os.path.join(self.repo, ".claude", "memory"))
        with open(os.path.join(self.repo, ".claude", "memory", "MEMORY.md"), "w") as fh:
            fh.write("# Hot cache\n\n- [2026-01-01] CANARY\n")
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=self.repo, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])

    def tearDown(self):
        for d in (self.repo, self.home, self.shim):
            shutil.rmtree(d, ignore_errors=True)

    def write(self, rel, text, base=None):
        path = os.path.join(base or self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def settings(self, perms, rel=".claude/settings.json", base=None):
        self.write(rel, json.dumps({"permissions": perms}), base)

    def context(self, source="startup"):
        r = subprocess.run(WIRING, shell=True, input=json.dumps({"session_id": "t", "source": source}),
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]

    def rails(self, source="startup"):
        return [ln for ln in self.context(source).splitlines() if ln.startswith("Rails:")]

    def test_clean_repo_is_silent(self):
        self.write(".env.example", "A=1\n")
        self.write(".env.sample", "A=1\n")
        for src in SOURCES:
            with self.subTest(source=src):
                self.assertEqual(self.rails(src), [])

    def test_uncovered_env_file_nudges_on_every_source_but_compact(self):
        self.write(".env", "SECRET=1\n")
        self.write("server.pem", "x\n")
        for src in SOURCES:
            with self.subTest(source=src):
                lines = self.rails(src)
                if src == "compact":
                    self.assertEqual(lines, [])
                    continue
                self.assertEqual(len(lines), 1, lines)
                self.assertIn("`.env`", lines[0])
                self.assertIn("`server.pem`", lines[0])
                self.assertIn("run `/memory-kit:setup rails`", lines[0])
                self.assertIn("touch .claude/state/rails-declined", lines[0])

    def test_read_deny_covers(self):
        self.write(".env", "S=1\n")
        self.write(".env.local", "S=1\n")
        self.write("k.pem", "x\n")
        self.settings({"deny": ["Read(./.env)", "Read(./.env.*)"]})
        self.settings({"deny": ["Read(./**/*.pem)"]}, rel=".claude/settings.local.json")
        self.assertEqual(self.rails(), [])

    def test_broad_allow_from_user_settings(self):
        self.assertEqual(self.rails(), [])
        self.settings({"allow": ["Bash(git *)", "Bash(git status)"]}, base=self.home)  # ~/.claude/settings.json
        lines = self.rails()
        self.assertEqual(len(lines), 1)
        self.assertIn("broad allow `Bash(git *)`", lines[0])
        self.assertNotIn("git status", lines[0])

    def test_broad_allow_forms(self):
        self.settings({"allow": ["Bash(*)", "Bash(python3:*)", "Bash(sh *)", "Bash(pnpm test)"]})
        line = self.rails()[0]
        for rule in ("Bash(*)", "Bash(python3:*)", "Bash(sh *)"):
            self.assertIn(rule, line)
        self.assertNotIn("pnpm test", line)

    def test_interpreter_over_a_path_wildcard_is_broad(self):
        self.settings({"allow": ["Bash(node scripts/*)", "Bash(python3 tools/*.py)",
                                 "Bash(bash scripts/stand.sh *)", "Bash(node scripts/build.mjs *)"]})
        line = self.rails()[0]
        self.assertIn("Bash(node scripts/*)", line)
        self.assertIn("Bash(python3 tools/*.py)", line)
        self.assertNotIn("stand.sh", line)
        self.assertNotIn("build.mjs", line)

    def test_markers_silence(self):
        self.write(".env", "S=1\n")
        for marker in ("rails-v2", "rails-declined"):
            with self.subTest(marker=marker):
                self.write(".claude/state/" + marker, "")
                self.assertEqual(self.rails(), [])
                os.remove(os.path.join(self.repo, ".claude", "state", marker))
        self.assertEqual(len(self.rails()), 1)

    def test_markers_survive_state_pruning(self):
        self.write(".env", "S=1\n")
        self.write(".claude/state/rails-declined", "")
        old = time.time() - 90 * 86400
        os.utime(os.path.join(self.repo, ".claude", "state", "rails-declined"), (old, old))
        self.context()
        self.assertTrue(os.path.exists(os.path.join(self.repo, ".claude", "state", "rails-declined")))

    def test_malformed_settings_never_break_the_hook(self):
        self.write(".env", "S=1\n")
        self.write(".claude/settings.json", "{not json")
        self.write(".claude/settings.local.json", json.dumps({"permissions": {"deny": "Read(./.env)"}}))
        self.assertEqual(len(self.rails()), 1)
        self.assertIn("CANARY", self.context())

    def test_unadopted_repo_gets_the_line_and_no_files(self):
        virgin = tempfile.mkdtemp(prefix="cmk-rails-virgin-")
        try:
            with open(os.path.join(virgin, ".env"), "w") as fh:
                fh.write("S=1\n")
            self.env["CLAUDE_PROJECT_DIR"] = virgin
            ctx = self.context()
            self.assertIn("not set up in this repository", ctx)
            self.assertEqual(len([ln for ln in ctx.splitlines() if ln.startswith("Rails:")]), 1)
            self.assertEqual(sorted(os.listdir(virgin)), [".env"])
        finally:
            shutil.rmtree(virgin, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
