#!/usr/bin/env python3
"""Tests for hooks/guard-secrets.py — run: python3 plugins/memory-kit/hooks/tests/test_guard_secrets.py

Every case feeds hook JSON through the EXACT command string registered in hooks.json (read from the
file, run by a shell with CLAUDE_PLUGIN_ROOT exported) — a hook proven any other way is not proven
wired. The `python3` that string names is pinned to the interpreter running these tests (a shim on
PATH), so `/usr/bin/python3 test_guard_secrets.py` proves the hook on 3.9.

What this proves: the hook's verdict on each command TEXT. What it cannot see: whether Claude Code
runs the hook for a given tool call (the release gate's headless probe does that).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MATCHER = "Read|Edit|Write|Bash"


def wiring(matcher, script):
    with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as fh:
        cfg = json.load(fh)
    for group in cfg["hooks"]["PreToolUse"]:
        if group.get("matcher") == matcher:
            for hook in group["hooks"]:
                if script in hook["command"]:
                    return hook
    raise AssertionError("%s is not wired under PreToolUse matcher %r" % (script, matcher))


HOOK = wiring(MATCHER, "guard-secrets.py")
WIRING = HOOK["command"]
PY_SHIM = tempfile.mkdtemp(prefix="cmk-py-")
os.symlink(sys.executable, os.path.join(PY_SHIM, "python3"))
BASE_ENV = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT, PATH=PY_SHIM + os.pathsep + os.environ["PATH"])
for _var in ("CMK_SECRETS_GUARD", "CMK_GIT_GUARD", "CMK_ALLOW_TEST_EDITS"):
    BASE_ENV.pop(_var, None)

# The spec's list first, then the neighbours of each mechanism.
BLOCKED = [
    "grep -rn foo .env",
    "rg SECRET -- .env.local",
    "grep -e x .env",
    "cat .env",
    "head -c 0 .env.local",
    "grep x .env",
    "sed -n 1p x/.env",
    "node -e \"require('fs').readFileSync('.env')\"",
    "python3 -c \"open('.env')\"",
    # every secret name
    "cat .env.production",
    "cat .env.development",
    "cat .env.test",
    "cat .env.staging",
    "cat .env.production.local",
    "cat certs/server.pem",
    "cat ~/.ssh/id_rsa",
    "cat ~/.ssh/id_rsa.pub",
    "openssl pkcs12 -in bundle.p12",
    "cat .ENV",
    # compound and wrapped forms
    "cd code/backend && cat .env",
    "ls && cat .env | head",
    "echo \"$(cat .env)\"",
    "bash -c 'cat .env'",
    "eval cat .env",
    "sudo cat /srv/app/.env",
    "env FOO=1 cat .env",
    "cat \"$HOME/proj/.env\"",
    "source .env && cat .env",
    # redirections are reads and writes too
    "cat < .env",
    "while read l; do echo $l; done < .env",
    "echo X=1 > .env",
    "cat .env >> notes.txt",
    "echo X=1 &> .env",
    # interpreters and inline scripts
    "python3 -c \"import pathlib; print(pathlib.Path('.env').read_text())\"",
    "node -p \"require('fs').readFileSync(__dirname + '/.env', 'utf8')\"",
    "perl -ne 'print' .env",
    "ruby -e 'puts File.read(\".env\")'",
    "python3 -Bc \"open('../.env').read()\"",
]

ALLOWED = [
    # an append writes without reading (owner 2026-10-20)
    "echo X=1 >> .env",
    "pbpaste | awk '{print}' >> .env",
    "source .env",
    "set -a; . ./.env; set +a; node app.js",
    "cp .env ../wt/.env",
    "cat .env.example",
    "cd code/backend && ls",
    "grep -rn foo src",
    "grep -rn '.env' src",
    "rg -n --hidden .env.local docs",
    "grep -rn -e .env src",
    "find . -name .env -maxdepth 2",
    # the other exempt commands
    "ln -s ../.env .env",
    "mv .env .env.bak",
    "ls -la .env",
    "test -f .env && echo yes",
    "[ -f .env ] && echo yes",
    "[[ -f .env ]] && echo yes",
    "git status .env",
    "git add .env.example",
    "rm .env.local",
    # not secret names
    "cat .env.sample",
    "cat .env.template",
    "cat src/env.ts",
    "cat docs/dotenv.md",
    "grep -rn 'rsa key' docs/",
    "cat keys/id_ed25519.pub.txt",
    # quoted prose is not a path, heredoc bodies are not commands
    "echo \"copy .env.example to .env\"",
    "git commit -m \"never cat .env\"",
    "cat > notes.md <<'EOF'\ncat .env is blocked\nEOF",
    # fast path and fail open
    "ls -la && npm test",
    "cat .env 'unterminated",
]


# AC-17 (spec amendment 2026-10-22): the append exemption covers ONLY a plain stdout append. Another fd's
# append stays blocked, and an append beside a file-descriptor path is a read on Linux (reopening
# /proc/self/fd/1 opens the appended file for reading).
APPEND_BYPASSES = [
    "echo X=1 2>> .env",
    "cat 3>> .env",
    "echo X=1 9>>.env.local",
    "cp /proc/self/fd/1 /tmp/x >> .env",
    "cat /proc/self/fd/1 >> .env",
    "cat /proc/12345/fd/1 >> .env",
    "cat /proc/thread-self/fd/1 >> .env",
    "cat /dev/fd/1 >> .env",
    "cat /dev/stdout >> .env",
    "cat /dev/stdin >> .env",
    "tee /dev/stderr >> .env",
    "cp /dev/fd/1 /tmp/x 1>> .env",
    "cp /dev/fd/1 /tmp/x &>> .env",
    # the fd path is in a sibling field or a nested command, not an argv word of the appending command
    "cat >> .env < /proc/self/fd/1",
    "{ cp /proc/self/fd/1 /tmp/x; } >> .env",
    "( cat /dev/fd/1 ) >> .env",
    "bash -c 'cp /proc/self/fd/1 /tmp/x' >> .env",
    "python3 -c \"print(open('/proc/self/fd/1').read())\" >> .env",
    # spelled differently, the same path
    "cat /proc/self//fd/1 >> .env",
    "cat /dev/./fd/1 >> .env",
    "cat /proc/self/x/../fd/1 >> .env",
    "cat /de\\v/fd/1 >> .env",
]

APPEND_ALLOWED = [
    "echo X=1 >> .env",
    "echo X=1 1>> .env",
    "echo X=1 &>> .env",
    "echo X=1 >> .env 2>&1",
    "printf 'A=1\\n' >> .env.local && echo done",
    # an fd path with no secret append is not this rule's business
    "cat /dev/stdin > notes.txt",
    "echo hi >> notes.txt; ls /dev/fd/",
]


class SecretsGuardTest(unittest.TestCase):
    def hook(self, tool, tool_input, env=None):
        payload = json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": tempfile.gettempdir()})
        r = subprocess.run(WIRING, shell=True, input=payload, capture_output=True, text=True, env=env or BASE_ENV)
        return r.returncode, r.stderr

    def bash(self, command, env=None):
        return self.hook("Bash", {"command": command}, env)

    def test_wiring(self):
        self.assertEqual(HOOK.get("timeout"), 10)

    def test_blocked_commands(self):
        for cmd in BLOCKED:
            with self.subTest(cmd=cmd):
                rc, err = self.bash(cmd)
                self.assertEqual(rc, 2, "expected block: %r (stderr %r)" % (cmd, err))
                self.assertIn("Memory Kit secrets guard:", err)
                self.assertIn("Set CMK_SECRETS_GUARD=off to disable.", err)

    def test_allowed_commands(self):
        for cmd in ALLOWED:
            with self.subTest(cmd=cmd):
                rc, err = self.bash(cmd)
                self.assertEqual(rc, 0, "expected allow: %r, stderr: %s" % (cmd, err))
                self.assertEqual(err, "")

    def test_append_bypasses_blocked(self):
        for cmd in APPEND_BYPASSES:
            with self.subTest(cmd=cmd):
                rc, err = self.bash(cmd)
                self.assertEqual(rc, 2, "expected block: %r (stderr %r)" % (cmd, err))
                self.assertIn("Memory Kit secrets guard:", err)

    def test_append_allowed(self):
        for cmd in APPEND_ALLOWED:
            with self.subTest(cmd=cmd):
                rc, err = self.bash(cmd)
                self.assertEqual(rc, 0, "expected allow: %r, stderr: %s" % (cmd, err))
                self.assertEqual(err, "")

    def test_fd_append_message_names_the_fd_path(self):
        _, err = self.bash("cp /proc/self/fd/1 /tmp/x >> .env")
        self.assertIn("/proc/self/fd/1", err)
        _, err = self.bash("echo X=1 2>> .env")
        self.assertIn("2>>", err)

    def test_file_tools(self):
        for tool in ("Read", "Edit", "Write"):
            for path, verdict in ((".env", 2), ("/repo/app/.env.local", 2), ("/repo/k.pem", 2),
                                  ("/repo/.env.example", 0), ("/repo/src/env.ts", 0)):
                with self.subTest(tool=tool, path=path):
                    rc, err = self.hook(tool, {"file_path": path})
                    self.assertEqual(rc, verdict, err)
        _, err = self.hook("Read", {"file_path": "/repo/.env"})
        self.assertIn("Read on `.env` blocked", err)

    def test_opt_out(self):
        env = dict(BASE_ENV, CMK_SECRETS_GUARD="off")
        self.assertEqual(self.bash("cat .env", env=env), (0, ""))
        self.assertEqual(self.hook("Read", {"file_path": ".env"}, env=env), (0, ""))

    def test_other_tools_pass(self):
        self.assertEqual(self.hook("Grep", {"pattern": "x", "path": ".env"})[0], 0)

    def test_garbage_stdin_fails_open(self):
        for raw in ("", "not json .env", '{"tool_name": "Bash", "tool_input": ".env"}'):
            with self.subTest(raw=raw):
                r = subprocess.run(WIRING, shell=True, input=raw, capture_output=True, text=True, env=BASE_ENV)
                self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
