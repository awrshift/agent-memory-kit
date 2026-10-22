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
    # `pbpaste | awk '{print}' >> .env` moved to APPEND_ALLOWLIST_BYPASSES (AC-17 amendment: allowlist only)
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

# AC-17 amendment (integrator, 2026-10-22, after a security review of the fd-path denylist): the append is exempt
# ONLY when every command in the line is echo / printf / a file-less cat fed by a quoted heredoc or a here-string,
# and nothing else reads a file. A list of fd-path spellings missed /proc/<pid>/task/<tid>/fd and fd paths read
# inside a heredoc, a here-string or an interpreter's stdin; the cases above stay as regression tests.
APPEND_ALLOWLIST_BYPASSES = [
    # reported: spellings the denylist did not know
    "cat /proc/1234/task/1234/fd/1 >> .env",
    "cp /proc/self/task/77/fd/1 /tmp/x >> .env",
    # reported: the fd path read where the parser never looks — a heredoc body, a here-string, stdin of an interpreter
    "python3 >> .env <<'EOF'\nprint(open('/proc/self/fd/1').read())\nEOF",
    "python3 <<< \"print(open('/proc/self/fd/1').read())\" >> .env",
    "sh >> .env <<'EOF'\ncat /proc/self/fd/1\nEOF",
    "cat <<EOF >> .env\n$(cat /proc/self/fd/1)\nEOF",
    "cat <<EOF >> .env\n`cat /proc/self/fd/1`\nEOF",
    # anything outside the allowlist with a secret append
    "pbpaste | awk '{print}' >> .env",
    "cat notes.txt >> .env",
    "echo X=1 >> .env < input.txt",
    "cat <&3 >> .env",
    "echo \"$(cat /proc/self/fd/1)\" >> .env",
    "printf '%s\\n' \"$(< /proc/self/fd/1)\" >> .env",
    "npm run gen-env && echo X=1 >> .env",
]

# AC-17, third round (integrator STOP SIGNAL, 2026-10-22): every "looks safe" exemption depended on the parser agreeing
# with the shell. The exemption now has no parser surface: ONE simple call, literally `echo` or `printf`, every word
# a literal (no `$`, backtick or unquoted glob), and exactly one redirection — `>>` or `1>>` to the secret file.
# The forms below were allowed by an earlier round of this branch (never released) and are blocked now.
APPEND_NARROWED = [
    # reported: cat with a dynamic argument, fd duplication, exec redirections, &>>
    "cat -$F >> .env",
    "echo X=1 >> .env 2>&1",
    "echo X=1 >&3 >> .env",
    "exec >> .env; echo X=1",
    "exec 3>>.env",
    "echo X=1 &>> .env",
    # dynamic words and globs
    "echo \"$X\" >> .env",
    "echo \"KEY=$v\" >> .env",
    "echo KEY=`id` >> .env",
    "echo KEY=$(id) >> .env",
    "printf '%s\\n' * >> .env",
    "echo KEY=a? >> .env",
    # more than one call, a wrapper, an assignment, a group
    "echo a >> .env; cat .env",
    "echo a >> .env; echo b",
    "printf 'A=1\\n' >> .env.local && echo done",
    "echo a | cat >> .env",
    "VAR=1 echo x >> .env",
    "command echo x >> .env",
    "sudo echo x >> .env",
    "( echo x ) >> .env",
    "{ echo x; } >> .env",
    "echo x >(cat) >> .env",
    # a second redirection, a heredoc or a here-string
    "echo KEY=v >> .env 2>/dev/null",
    "echo KEY=v >> .env >> other.txt",
    "cat <<'EOF' >> .env\nKEY=1\nEOF",
    "cat >> .env <<< \"KEY=v\"",
    "echo KEY=v >> .env <<< x",
    # the name must be literally echo / printf
    "/bin/echo KEY=v >> .env",
    "cat - >> .env",
]

APPEND_ALLOWED = [
    "echo X=1 >> .env",
    "echo 'KEY=value' >> .env",
    "printf '%s\\n' 'KEY=v' >> .env",
    "echo KEY=v 1>> .env",
    "printf '%s\\n' x >> .env.local",
    "echo \"KEY=a b\" >>.env",
    "echo 'KEY=$NOT_EXPANDED' >> .env",
    "echo 'glob*literal' >> .env",
    # quoted digits before a redirection are an argument, not an fd (cmdparse fix, third round)
    "echo KEY=v '2'>> .env",
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

    def test_append_allowlist_bypasses_blocked(self):
        for cmd in APPEND_ALLOWLIST_BYPASSES:
            with self.subTest(cmd=cmd):
                rc, err = self.bash(cmd)
                self.assertEqual(rc, 2, "expected block: %r (stderr %r)" % (cmd, err))
                self.assertIn("Memory Kit secrets guard:", err)

    def test_append_narrowed_to_one_literal_echo(self):
        for cmd in APPEND_NARROWED:
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

    def test_block_message_names_the_operator_and_the_exemption(self):
        _, err = self.bash("cp /proc/self/fd/1 /tmp/x >> .env")
        self.assertIn("redirection `>>` on `.env` blocked", err)
        self.assertIn("one literal `echo` / `printf`", err)
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


class LiteralAppendIsLazy(unittest.TestCase):
    """R2-9 (v7.3 r2), in-process: the literal-append exemption is evaluated only when a call has a secret
    redirection target. What this proves: when `literal_append` runs. Verdicts are the hook-level tests above."""

    def test_literal_append_only_on_a_secret_redirect(self):
        import importlib.util
        from unittest import mock

        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("guard_secrets_r2", os.path.join(PLUGIN_ROOT, "hooks",
                                                                                     "guard-secrets.py"))
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        for cmd, called, verdict in (
            ("cat .env.example && grep -rn x src", False, False),
            ("cat .env", False, True),
            ("echo x > notes.txt; ls .env", False, False),
            ("echo 'K=v' >> .env", True, False),
            ("cat x >> .env", True, True),
        ):
            with self.subTest(cmd=cmd), mock.patch.object(guard, "literal_append",
                                                          wraps=guard.literal_append) as spy:
                found = guard.secret_in_command(cmd, "/tmp")
                self.assertEqual(spy.called, called)
                self.assertEqual(bool(found), verdict)


if __name__ == "__main__":
    unittest.main(verbosity=1)
