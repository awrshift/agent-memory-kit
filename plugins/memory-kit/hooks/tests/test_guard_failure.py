#!/usr/bin/env python3
"""How the two policy guards fail (AC-3, v7.3) — run: python3 plugins/memory-kit/hooks/tests/test_guard_failure.py

Claude Code (v2.1.295+) blocks the tool call when a hook with `"onFailure": "block"` cannot start, exits with a
code other than 0/2, times out or prints invalid output. Both guards (`guard-secrets.py`, `guard-git.py`) carry it.
To keep a bug in a guard from blocking EVERY call, each guard turns its own internal exception into an explicit
`permissionDecision: "ask"` naming the guard and the error (exit 0), and the wiring checks that `python3` exists
first, so a machine without it gets an explicit no-op instead of a bricked session.

Every case runs the EXACT command string from hooks.json through a shell. An internal exception is produced by
a copy of the plugin's hooks/ whose `lib/cmdparse.py` raises — the guard code itself is the shipped file.

What this proves: the verdict each failure mode prints, and the wiring fields. What it cannot see: that Claude
Code honours `onFailure` (the platform doc does; an older Claude Code accepting the field is AC-4's probe).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUARDS = {
    # script: (matcher, a payload the guard must parse past its fast path, guard label in the reason)
    "guard-secrets.py": ("Read|Edit|Write|Bash", {"tool_name": "Bash", "tool_input": {"command": "cat x.env.local"}},
                         "secrets guard"),
    "guard-git.py": ("Bash", {"tool_name": "Bash", "tool_input": {"command": "git push origin x"}}, "git guard"),
}


def wired_hook(matcher, script):
    with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as fh:
        cfg = json.load(fh)
    for group in cfg["hooks"]["PreToolUse"]:
        if group.get("matcher") == matcher:
            for hook in group["hooks"]:
                if script in hook["command"]:
                    return hook
    raise AssertionError("%s is not wired under PreToolUse matcher %r" % (script, matcher))


class GuardFailureTest(unittest.TestCase):
    def setUp(self):
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        self.env = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT, PATH=self.shim + os.pathsep + os.environ["PATH"])
        for var in ("CMK_SECRETS_GUARD", "CMK_GIT_GUARD", "CMK_ALLOW_TEST_EDITS"):
            self.env.pop(var, None)
        self.broken = None

    def tearDown(self):
        shutil.rmtree(self.shim, ignore_errors=True)
        if self.broken:
            shutil.rmtree(self.broken, ignore_errors=True)

    def run_hook(self, script, payload, env):
        matcher = GUARDS[script][0]
        cmd = wired_hook(matcher, script)["command"]
        return subprocess.run(cmd, shell=True, input=json.dumps(payload), capture_output=True, text=True, env=env)

    def broken_plugin(self, body):
        """A copy of the plugin whose lib/cmdparse.py is replaced by `body`."""
        self.broken = tempfile.mkdtemp(prefix="cmk-broken-")
        shutil.copytree(os.path.join(PLUGIN_ROOT, "hooks"), os.path.join(self.broken, "hooks"))
        with open(os.path.join(self.broken, "hooks", "lib", "cmdparse.py"), "w") as fh:
            fh.write(body)
        return dict(self.env, CLAUDE_PLUGIN_ROOT=self.broken)

    def assert_ask(self, r, label, needle):
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn(label, out["permissionDecisionReason"])
        self.assertIn(needle, out["permissionDecisionReason"])

    def test_both_guards_block_on_failure_and_protect_tests_does_not(self):
        for script, (matcher, _, _) in GUARDS.items():
            with self.subTest(script=script):
                self.assertEqual(wired_hook(matcher, script).get("onFailure"), "block")
        self.assertNotIn("onFailure", wired_hook("Edit|Write", "protect-tests.py"))

    def test_internal_exception_asks_never_passes_silently(self):
        env = self.broken_plugin(
            "def commands(command, cwd):\n    raise RuntimeError('boom-in-parser')\n"
            "def git_calls(command, cwd):\n    raise RuntimeError('boom-in-parser')\n"
        )
        for script, (_, payload, label) in GUARDS.items():
            with self.subTest(script=script):
                self.assert_ask(self.run_hook(script, payload, env), label, "boom-in-parser")

    def test_missing_parser_module_asks(self):
        env = self.broken_plugin("raise ImportError('cmdparse-missing')\n")
        for script, (_, payload, label) in GUARDS.items():
            with self.subTest(script=script):
                self.assert_ask(self.run_hook(script, payload, env), label, "cmdparse-missing")

    def test_nesting_past_the_parser_depth_asks(self):
        """A command nested deeper than the parser follows is one the shell WOULD run: not a fail-open case."""
        cases = {
            "guard-secrets.py": "cat .env",
            "guard-git.py": "git reset --hard",
        }
        for script, inner in cases.items():
            cmd = inner
            for _ in range(10):
                cmd = "eval %s" % cmd
            payload = {"tool_name": "Bash", "tool_input": {"command": cmd}}
            with self.subTest(script=script):
                self.assert_ask(self.run_hook(script, payload, self.env), GUARDS[script][2], "nesting")

    def test_unterminated_quote_still_fails_open(self):
        for script, cmd in (("guard-secrets.py", "cat .env 'x"), ("guard-git.py", "git reset --hard 'x")):
            with self.subTest(script=script):
                r = self.run_hook(script, {"tool_name": "Bash", "tool_input": {"command": cmd}}, self.env)
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_no_python3_is_an_explicit_no_op(self):
        empty = tempfile.mkdtemp(prefix="cmk-nopath-")
        try:
            env = dict(self.env, PATH=empty)
            for script, (_, payload, _) in GUARDS.items():
                with self.subTest(script=script):
                    r = self.run_hook(script, payload, env)
                    self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        finally:
            shutil.rmtree(empty, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
