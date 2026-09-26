#!/usr/bin/env python3
"""Tests for hooks/guard-git.py — run: python3 plugins/memory-kit/hooks/tests/test_guard_git.py

Every case feeds hook JSON through the EXACT command string registered in hooks.json (read from the
file, run by a shell with CLAUDE_PLUGIN_ROOT exported) — a hook proven any other way is not proven
wired. The `python3` that string names is pinned to the interpreter running these tests (a shim on
PATH), so `/usr/bin/python3 test_guard_git.py` proves the hook on 3.9.
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


def wiring(matcher, script):
    with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as fh:
        cfg = json.load(fh)
    for group in cfg["hooks"]["PreToolUse"]:
        if group.get("matcher") == matcher:
            for hook in group["hooks"]:
                if script in hook["command"]:
                    return hook["command"]
    raise AssertionError("%s is not wired under PreToolUse matcher %r" % (script, matcher))


WIRING = wiring("Bash", "guard-git.py")
PY_SHIM = tempfile.mkdtemp(prefix="cmk-py-")
os.symlink(sys.executable, os.path.join(PY_SHIM, "python3"))
BASE_ENV = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT, PATH=PY_SHIM + os.pathsep + os.environ["PATH"])
BASE_ENV.pop("CMK_GIT_GUARD", None)

BLOCKED = [
    "git push --force origin feat",
    "git push -f origin feat",
    "git push -uf origin feat",
    "git push origin feat --force",
    "git push origin +feat",
    "git push origin +HEAD:refs/heads/feat",
    "git push --force-with-lease --force origin feat",
    "git push --mirror backup",
    "git reset --hard",
    "git reset -q --hard origin/main",
    "git clean -f",
    "git clean -fd",
    "git clean -fdx",
    "git clean -xdf",
    "git clean --force -d",
    "git branch -D feat",
    "git branch --delete --force feat",
    "git branch -d -f feat",
    "git checkout .",
    "git checkout -- .",
    "git checkout HEAD -- .",
    "git restore .",
    "git restore --staged --worktree .",
    "git restore -SW .",
    # unwrapping / compound forms
    "cd /tmp && git reset --hard",
    "git -C /some/repo reset --hard HEAD~1",
    "git --no-pager -c core.pager=cat clean -fdx",
    "bash -c 'git clean -fdx'",
    "sh -lc \"cd x; git branch -D feat\"",
    "GIT_DIR=.git git branch -D feat",
    "env GITHUB_TOKEN= git push -f origin feat",
    "command git reset --hard",
    'echo "$(git reset --hard)"',
    "true; git checkout .",
    "git status | cat\ngit restore .",
    "if true; then git reset --hard; fi",
    "echo hi # a note\ngit reset --hard",
    "eval git clean -f",
    # a directory the shell computes must not make the guard fail open (board fix)
    'cd "$(mktemp -d)" && git push -f origin x',
    "git -C $(pwd) push -f origin x",
    "git -C `pwd` reset --hard",
    "pushd $(git rev-parse --show-toplevel) && git clean -fdx",
    # wrappers, each after its own options
    "timeout 5 git push -f origin x",
    "timeout -s KILL --preserve-status 30s git reset --hard",
    "nice -n 10 git clean -fdx",
    "nice git branch -D feat",
    "nohup git push --force origin x",
    "sudo -u deploy git reset --hard",
    "sudo -E GIT_TRACE=1 git push -f origin x",
    "echo feat | xargs git branch -D",
    "echo feat | xargs -I{} git push -f origin {}",
    "find . -name x | xargs -0 -n 1 git push --force origin",
    "time -p git push -f origin x",
]

ALLOWED = [
    "git push --force-with-lease origin feat",
    "git push --force-with-lease=feat:0123abcd origin feat",
    "git push --force-with-lease --force-if-includes origin feat",
    "git push --force-if-includes --force-with-lease=feat upstream feat",
    "git push --force-if-includes origin feat",
    "git push origin feat",
    "git push -o ci.skip origin feat",
    "git reset --soft HEAD~1",
    "git reset HEAD src/a.ts",
    "git clean -n",
    "git branch -d feat",
    "git checkout feat",
    "git checkout -b feat",
    "git checkout -- src/a.ts",
    "git restore src/a.ts",
    "git restore --staged .",
    "timeout 5 git push origin feat",
    "sudo -u deploy git status",
    # quoted / heredoc / argument text is not a git argv
    "cat >> f <<'EOF'\nthen run git reset --hard and git push --force\nEOF",
    'git commit -m "no reset --hard here"',
    'git commit -m "git push -f origin main would be bad"',
    'echo "git push --force"',
    "echo git reset --hard",
    'grep -n "reset --hard" notes.md',
    "grep -rn 'git push -f' docs/",
    "git commit -m \"$(cat <<'EOF'\nAC-NONE: don't git clean -fdx (really)\nEOF\n)\"",
    "printf '%s\\n' 'git branch -D x'",
    # not git at all (fast path)
    "ls -la && npm test",
    # fail open: the shell would not run an unbalanced command either
    'git reset --hard "unterminated',
    "git push -f 'unterminated",
]


class GitGuardTest(unittest.TestCase):
    def hook(self, command, tool="Bash", env=None):
        payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}, "cwd": tempfile.gettempdir()})
        r = subprocess.run(WIRING, shell=True, input=payload, capture_output=True, text=True, env=env or BASE_ENV)
        return r.returncode, r.stderr

    def test_blocked_forms(self):
        for cmd in BLOCKED:
            with self.subTest(cmd=cmd):
                rc, err = self.hook(cmd)
                self.assertEqual(rc, 2, "expected block: %r (stderr %r)" % (cmd, err))
                self.assertIn("Memory Kit git guard:", err)
                self.assertIn("Set CMK_GIT_GUARD=off to disable.", err)

    def test_allowed_forms(self):
        for cmd in ALLOWED:
            with self.subTest(cmd=cmd):
                rc, err = self.hook(cmd)
                self.assertEqual(rc, 0, "expected allow: %r, stderr: %s" % (cmd, err))
                self.assertEqual(err, "")

    def test_message_names_the_operation(self):
        _, err = self.hook("git push -f origin feat")
        self.assertIn("`git push --force` blocked", err)
        self.assertIn("force-with-lease", err)
        _, err = self.hook("git clean -fdx")
        self.assertIn("`git clean -f` blocked", err)
        self.assertIn("untracked", err)
        _, err = self.hook("git push --mirror backup")
        self.assertIn("`git push --mirror` blocked", err)

    def test_opt_out(self):
        env = dict(BASE_ENV, CMK_GIT_GUARD="off")
        for cmd in ("git push --force origin x", "git reset --hard"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.hook(cmd, env=env), (0, ""))

    def test_non_bash_tool_allowed(self):
        rc, _ = self.hook("git reset --hard", tool="Write")
        self.assertEqual(rc, 0)

    def test_garbage_stdin_fails_open(self):
        for raw in ("", "not json with git", '{"tool_input": "git"}'):
            with self.subTest(raw=raw):
                r = subprocess.run(WIRING, shell=True, input=raw, capture_output=True, text=True, env=BASE_ENV)
                self.assertEqual(r.returncode, 0)

    def test_never_spawns_git(self):
        root = tempfile.mkdtemp(prefix="cmk-guard-")
        try:
            mark = os.path.join(root, "spawned")
            with open(os.path.join(root, "git"), "w") as f:
                f.write('#!/bin/sh\ntouch "%s"\nexec "%s" "$@"\n' % (mark, shutil.which("git")))
            os.chmod(os.path.join(root, "git"), 0o755)
            env = dict(BASE_ENV, PATH=root + os.pathsep + BASE_ENV["PATH"])
            start = time.time()
            for cmd in ("git reset --hard", "git push --force-with-lease origin feat", "git status"):
                self.hook(cmd, env=env)
            self.assertFalse(os.path.exists(mark))
            self.assertLess(time.time() - start, 5)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PY_SHIM, ignore_errors=True)
