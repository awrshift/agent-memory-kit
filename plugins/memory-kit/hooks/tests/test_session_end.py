#!/usr/bin/env python3
"""SessionEnd fits the platform's budget (AC-5, v7.3) — run: python3 plugins/memory-kit/hooks/tests/test_session_end.py

Platform fact (code.claude.com/docs/en/hooks §SessionEnd, read 2026-10-22): SessionEnd hooks share a 1.5-second
budget, and "Timeouts set on plugin-provided hooks don't raise the budget" — a plugin's `timeout: 15` was a number
nothing honoured. hooks.json now states 1, and the script must finish well inside 1.5 s even when Claude Code never
writes or closes its stdin.

Every case runs the EXACT SessionEnd command from hooks.json. What this proves: the configured number and the
script's wall time on this machine (5 runs; the worst must stay under 60 % of the budget, room for Claude Code's own overhead). What it cannot see: Claude Code's own
overhead around the hook on a loaded machine.
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
    HOOK = json.load(_fh)["hooks"]["SessionEnd"][0]["hooks"][0]
BUDGET_S = 1.5


class SessionEnd(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="cmk-end-repo-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        os.makedirs(os.path.join(self.repo, ".claude", "memory"))
        with open(os.path.join(self.repo, ".claude", "memory", "MEMORY.md"), "w") as fh:
            fh.write("# Hot\n")
        self.env = dict(os.environ, CLAUDE_PROJECT_DIR=self.repo, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        self.env.pop("CLAUDE_INVOKED_BY", None)

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)
        shutil.rmtree(self.shim, ignore_errors=True)

    def log(self):
        with open(os.path.join(self.repo, ".claude", "state", "session-end.log")) as fh:
            return fh.read()

    def test_configured_timeout_is_inside_the_shared_budget(self):
        self.assertLessEqual(HOOK["timeout"], BUDGET_S)

    def test_open_stdin_still_finishes_inside_the_budget(self):
        worst = 0.0
        for _ in range(5):
            start = time.time()
            p = subprocess.Popen(HOOK["command"], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=self.env)
            p.wait(timeout=10)  # stdin is never written or closed while it runs
            worst = max(worst, time.time() - start)
            p.stdin.close()
            self.assertEqual(p.returncode, 0)
        self.assertLess(worst, BUDGET_S * 0.6, "worst run %.3f s" % worst)
        self.assertIn("session=unknown", self.log())

    def test_payload_is_logged(self):
        r = subprocess.run(HOOK["command"], shell=True, input=json.dumps({"session_id": "abc-1", "reason": "other"}),
                           capture_output=True, text=True, env=self.env, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("session=abc-1", self.log())


if __name__ == "__main__":
    unittest.main(verbosity=1)
