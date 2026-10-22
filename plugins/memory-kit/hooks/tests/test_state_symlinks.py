#!/usr/bin/env python3
"""No kit hook writes through a symlink under .claude/state (integrator amendment, v7.3) — run:
python3 plugins/memory-kit/hooks/tests/test_state_symlinks.py

A cloned repository can ship `.claude/state` (or a file in it, or `.claude` itself) as a symlink to, say,
~/.bashrc; a hook that appends a log line or replaces a counter there would then write the target. Every write
the hooks make under .claude/state goes through one helper per language (`hooks/lib/statefs.py`,
`hooks/lib/state.sh`): it refuses — silently, the hook still succeeds — when `.claude` or `.claude/state` or the
target entry is a symlink, or when the state directory resolves outside the project; replacements go through a
fresh temp file in the state directory, never a fixed name.

Every case runs the EXACT hook commands from hooks.json (SessionStart parts 1..6 on startup and compact,
PreCompact auto and manual, SessionEnd, protect-tests on a new test file) and then compares the symlink targets
byte for byte and by mtime. What this proves: those hooks leave the targets untouched and still exit 0. What it
cannot see: a symlink swapped in WHILE a hook runs (the append opens with O_NOFOLLOW; the replace re-checks).
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
    _CFG = json.load(_fh)["hooks"]
PARTS = [h["command"] for h in _CFG["SessionStart"][0]["hooks"]]
PRECOMPACT = _CFG["PreCompact"][0]["hooks"][0]["command"]
SESSION_END = _CFG["SessionEnd"][0]["hooks"][0]["command"]
PROTECT = [h["command"] for g in _CFG["PreToolUse"] for h in g["hooks"] if "protect-tests.py" in h["command"]][0]
STATE_NAMES = ("session_count", "session_last", "compact-unsaved", "compact-unsaved-seen", "hook.log",
               "session-end.log", "sess-1_created_tests", "old-bookkeeping")


class StateSymlinks(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="cmk-sym-repo-")
        self.outside = tempfile.mkdtemp(prefix="cmk-sym-outside-")
        self.home = tempfile.mkdtemp(prefix="cmk-sym-home-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=self.repo, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        for var in ("CMK_INJECT_BUDGET", "CMK_ALLOW_TEST_EDITS"):
            self.env.pop(var, None)

    def tearDown(self):
        for d in (self.repo, self.outside, self.home, self.shim):
            shutil.rmtree(d, ignore_errors=True)

    def put(self, path, text, old=False):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        if old:
            os.utime(path, (1, 1))

    def adopt(self, claude_dir=None):
        claude = claude_dir or os.path.join(self.repo, ".claude")
        self.put(os.path.join(claude, "memory", "MEMORY.md"), "# Hot\n\n- [2026-01-01] CANARY\n")
        os.utime(os.path.join(claude, "memory", "MEMORY.md"), (1, 1))  # stale: pre-compact writes
        self.put(os.path.join(self.repo, "context", "handoffs", "h-2026-01-01.md"), "# Handoff\n")

    def snapshot(self, root):
        snap = {}
        for base, dirs, files in os.walk(root):
            for name in dirs + files:
                path = os.path.join(base, name)
                st = os.lstat(path)
                body = open(path, "rb").read() if os.path.isfile(path) and not os.path.islink(path) else None
                snap[os.path.relpath(path, root)] = (st.st_mtime_ns, body)
        return snap

    def run_all_hooks(self):
        def sh(cmd, payload):
            r = subprocess.run(cmd, shell=True, input=json.dumps(payload), capture_output=True, text=True,
                               env=self.env, timeout=30)
            self.assertEqual(r.returncode, 0, "%s: %s" % (cmd, r.stderr))
            return r.stdout

        for source in ("startup", "compact"):
            for cmd in PARTS:
                sh(cmd, {"session_id": "sess-1", "source": source})
        sh(PRECOMPACT, {"session_id": "sess-1", "trigger": "auto"})
        sh(PRECOMPACT, {"session_id": "sess-1", "trigger": "manual"})
        for source in ("compact", "startup"):
            for cmd in PARTS:
                sh(cmd, {"session_id": "sess-1", "source": source})
        sh(SESSION_END, {"session_id": "sess-1", "reason": "other"})
        sh(PROTECT, {"session_id": "sess-1", "tool_name": "Write",
                     "tool_input": {"file_path": os.path.join(self.repo, "tests", "test_new.py"), "content": "x"}})

    def victim_files(self, directory):
        """The names the hooks write, as files in `directory` with known text (the marker in its valid format)."""
        for name in STATE_NAMES:
            text = "VICTIM %s\n" % name
            if name == "compact-unsaved":
                text = time.strftime("%Y-%m-%d %H:%M:%S") + "\tstale\n"
            self.put(os.path.join(directory, name), text, old=(name == "old-bookkeeping"))

    def test_symlinked_state_dir_is_never_written(self):
        self.adopt()
        target = os.path.join(self.outside, "state-target")
        self.victim_files(target)
        os.symlink(target, os.path.join(self.repo, ".claude", "state"))
        before = self.snapshot(self.outside)
        self.run_all_hooks()
        self.assertEqual(self.snapshot(self.outside), before)

    def test_symlinked_state_files_are_never_written(self):
        self.adopt()
        state = os.path.join(self.repo, ".claude", "state")
        os.makedirs(state)
        self.victim_files(self.outside)
        for name in STATE_NAMES:
            os.symlink(os.path.join(self.outside, name), os.path.join(state, name))
        before = self.snapshot(self.outside)
        self.run_all_hooks()
        self.assertEqual(self.snapshot(self.outside), before)
        # nothing was dropped beside them either: no temp file left behind
        self.assertEqual(sorted(os.listdir(state)), sorted(STATE_NAMES))

    def test_symlinked_claude_dir_gets_no_state_created_outside(self):
        target = os.path.join(self.outside, "dot-claude")
        self.adopt(claude_dir=target)
        os.symlink(target, os.path.join(self.repo, ".claude"))
        before = self.snapshot(self.outside)
        self.run_all_hooks()
        self.assertEqual(self.snapshot(self.outside), before)

    def test_a_real_state_dir_is_still_written(self):
        """The guard must not switch the bookkeeping off for a normal repository."""
        self.adopt()
        self.run_all_hooks()
        state = os.path.join(self.repo, ".claude", "state")
        for name in ("session_count", "session_last", "hook.log", "session-end.log", "sess-1_created_tests"):
            self.assertTrue(os.path.isfile(os.path.join(state, name)), name)
        self.assertFalse([n for n in os.listdir(state) if n.startswith(".") and n != ".gitkeep"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
