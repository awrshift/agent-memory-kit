#!/usr/bin/env python3
"""How the two policy guards fail (AC-3, v7.3) — run: python3 plugins/memory-kit/hooks/tests/test_guard_failure.py

Claude Code (v2.1.295+) blocks the tool call when a hook with `"onFailure": "block"` cannot start, exits with a
code other than 0/2, times out or prints invalid output. Both guards (`guard-secrets.py`, `guard-git.py`) carry it.
To keep a bug in a guard from blocking EVERY call, each guard turns its own internal exception into an explicit
`permissionDecision: "ask"` naming the guard and the error (exit 0), and the wiring first proves `python3` RUNS
(7.3 r2: `python3 -c '…' || exit 0`, not `command -v` — the macOS stub exists and exits 1), so a machine without a
working python3 gets an explicit no-op instead of a bricked session.

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


# R2-1 (v7.3): every guard's command first proves python3 RUNS, not only that a file named python3 exists — the
# macOS /usr/bin/python3 is a stub that exists and exits 1 without the developer tools, and under
# `onFailure: block` a guard failing that way would block every Bash/Read/Edit/Write call.
RUNS_CHECK = "python3 -c 'import sys; sys.exit(sys.version_info < (3,9))' >/dev/null 2>&1 || exit 0; "
OLD_CHECK = "command -v python3 >/dev/null 2>&1 || exit 0; "
ALL_GUARDS = (("Read|Edit|Write|Bash", "guard-secrets.py"), ("Bash", "guard-git.py"), ("Bash", "guard-zsh-split.py"))
REPO_ROOT = os.path.dirname(os.path.dirname(PLUGIN_ROOT))
CHECK_REPO = os.path.join(REPO_ROOT, "tools", "check-repo.py")


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

    def test_every_guard_checks_that_python3_runs(self):
        """R2-1: the wiring itself — all three guards start with the runs-check, none with `command -v`."""
        for matcher, script in ALL_GUARDS:
            with self.subTest(script=script):
                cmd = wired_hook(matcher, script)["command"]
                self.assertTrue(cmd.startswith(RUNS_CHECK), cmd)
                self.assertNotIn("command -v", cmd)

    def test_a_python3_that_exists_but_cannot_run_is_a_no_op(self):
        """R2-1: a `python3` on PATH that exits 1 (the macOS stub without the developer tools) → exit 0, no output,
        so `onFailure: block` never fires on it. The pre-7.3-r2 `command -v` check passed the stub and the guard
        then exited 1."""
        stub_dir = tempfile.mkdtemp(prefix="cmk-stub-")
        try:
            stub = os.path.join(stub_dir, "python3")
            with open(stub, "w") as fh:
                fh.write("#!/bin/sh\necho 'xcrun: error: invalid active developer path' >&2\nexit 1\n")
            os.chmod(stub, 0o755)
            env = dict(self.env, PATH=stub_dir)
            payloads = {script: payload for script, (_, payload, _) in GUARDS.items()}
            payloads["guard-zsh-split.py"] = {"tool_name": "Bash", "tool_input": {"command": 'a="x y"; set -- $a'}}
            for matcher, script in ALL_GUARDS:
                with self.subTest(script=script):
                    cmd = wired_hook(matcher, script)["command"]
                    r = subprocess.run(cmd, shell=True, input=json.dumps(payloads[script]), capture_output=True,
                                       text=True, env=env)
                    self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        finally:
            shutil.rmtree(stub_dir, ignore_errors=True)

    @unittest.skipUnless(os.path.isfile(CHECK_REPO), "tools/check-repo.py ships with the repo, not the plugin")
    def test_check_repo_rejects_a_guard_without_the_runs_check(self):
        """R2-1 mutation: check-repo §3 fails when a guard's command uses the old `command -v` form or no check at
        all, and passes the shipped hooks.json. Runs check-repo on a copy of the repo without .git and media (the
        image checks may fail on that copy; only the hooks.json lines are read)."""
        def run(mutate):
            tmp = tempfile.mkdtemp(prefix="cmk-check-repo-")
            try:
                shutil.copytree(REPO_ROOT, os.path.join(tmp, "repo"), ignore=shutil.ignore_patterns(
                    ".git", "__pycache__", ".pytest_cache", "*.gif", "*.mp4", "*.png", "*.jpg", "*.webp"))
                path = os.path.join(tmp, "repo", "plugins", "memory-kit", "hooks", "hooks.json")
                with open(path) as fh:
                    text = fh.read()
                with open(path, "w") as fh:
                    fh.write(mutate(text))
                r = subprocess.run([sys.executable, os.path.join(tmp, "repo", "tools", "check-repo.py")],
                                   capture_output=True, text=True)
                return [ln for ln in (r.stdout + r.stderr).splitlines() if "hooks.json [PreToolUse]" in ln]
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

        self.assertEqual(run(lambda t: t), [])
        for label, mutate in (
            ("old command -v form", lambda t: t.replace(RUNS_CHECK, OLD_CHECK, 1)),
            ("no check at all", lambda t: t.replace(RUNS_CHECK, "", 1)),
        ):
            with self.subTest(mutation=label):
                lines = run(mutate)
                self.assertTrue(lines, "check-repo accepted the %s" % label)
                self.assertTrue(any("guard-" in ln for ln in lines), lines)


if __name__ == "__main__":
    unittest.main(verbosity=1)
