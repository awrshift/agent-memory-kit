#!/usr/bin/env python3
"""PreToolUse(Read|Edit|Write|Bash) — the Memory Kit secrets guard: keeps secret files out of the transcript.

Why a hook and not a `Read` deny rule: a Read deny on env files makes Claude Code's static check ASK
on harmless shell commands in some repos (`cd code/backend && ls` in a repo with nested worktrees;
reproduced headless 2026-09-26: Read deny on → asks, Edit-only → runs), so projects dropped the
deny and lost the control. A hook gates the same reads without touching that static check.

Secret names (basename, case-insensitive): `.env`, `.env.local`, `.env.*.local`,
`.env.development|production|test|staging`, `*.pem`, `id_rsa*`, `*.p12`. Not secret:
`.env.example`, `.env.sample`, `.env.template` (and any other `.env.<name>`).

Blocked (exit 2 + reason on stderr):
  Read / Edit / Write   whose `file_path` basename is a secret name;
  Bash                  a command (found by `lib/cmdparse.py`: `&&`, pipes, `$(…)`, `bash -c`,
                        `eval`, `sudo`/`env`/`xargs`… unwrapped) with an argv word whose basename is
                        a secret name, or a file redirection to/from one (`< .env`, `> .env`);
                        a word after an inline-script option (`-e`, `-c`, `-E`, `-p`, `-r`, `--eval`,
                        `--print`, `--command`, a short cluster ending in c/e) and every word of an
                        interpreter (node, python, perl, ruby, php, deno, bun, …) is also split into
                        path-like tokens, so `node -e "fs.readFileSync('.env')"` counts.
Allowed commands whatever their arguments: `source` / `.` (loading into a process), `cp` / `ln` /
`mv` (moving the file whole — an executor copying the env into its worktree), `ls`, `test` / `[` /
`[[`, `git`, `rm`.
Opt-out: CMK_SECRETS_GUARD=off in the environment.
Failure policy: fail OPEN on a parse error (an unbalanced quote is also a command the shell refuses).
Known gaps: globs (`cat .e*`), heredoc bodies fed to an interpreter (`python3 - <<EOF`), script
files, a copy read afterwards (`cp .env x && cat x`), tools outside the matcher (Grep, NotebookEdit).
Known false positives: a secret NAME used as a non-path argument (`grep -rn '.env' src`,
`find . -name .env`) — the word cannot be told from a path.
Python 3.9+, stdlib only; never spawns a process.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.dont_write_bytecode = True  # the plugin directory is not ours to litter with __pycache__

SECRET_RE = re.compile(
    r"^(?:\.env(?:\.local|\..+\.local|\.(?:development|production|test|staging))?|.+\.pem|id_rsa.*|.+\.p12)$"
)
FAST_PATH = (".env", ".pem", "id_rsa", ".p12")
EXEMPT = {"source", ".", "cp", "ln", "mv", "ls", "test", "[", "[[", "git", "rm"}
SCRIPT_OPTS = {"-e", "-c", "-E", "-p", "-r", "--eval", "--print", "--command"}
INTERPRETER_RE = re.compile(r"^(?:node(?:js)?|deno|bun|python[\d.]*|pypy[\d.]*|perl|ruby|php|lua|osascript)$")
NOT_PATH_RE = re.compile(r"[^A-Za-z0-9._\-/~@%$\x00]+")


def is_secret(path):
    return bool(SECRET_RE.match(os.path.basename(str(path)).lower()))


def _script_word(prev):
    if prev in SCRIPT_OPTS:
        return True
    return len(prev) > 1 and prev[0] == "-" and prev[1] != "-" and prev[-1] in "ce"


def secret_in_command(command, cwd):
    """(command name, secret word) for the first blocked use, or None."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
    import cmdparse

    for call in cmdparse.commands(command, cwd):
        for target in call.get("redirects", ()):
            if is_secret(target):
                return "redirection", str(target)
        name = call["name"]
        if name is None or name in EXEMPT:
            continue
        argv = [str(w) for w in call["argv"]]
        interpreter = bool(INTERPRETER_RE.match(name))
        for k, word in enumerate(argv):
            if is_secret(word):
                return name, word
            if interpreter or (k > 0 and _script_word(argv[k - 1])):
                for token in NOT_PATH_RE.split(word):
                    if token and is_secret(token):
                        return name, token
    return None


def main():
    if os.environ.get("CMK_SECRETS_GUARD", "").lower() == "off":
        return 0
    try:
        raw = sys.stdin.read()
        low = raw.lower()
        if not any(marker in low for marker in FAST_PATH):
            return 0
        data = json.loads(raw)
        tool = data.get("tool_name")
        tool_input = data.get("tool_input") or {}
        found = None
        if tool in ("Read", "Edit", "Write"):
            path = tool_input.get("file_path")
            if isinstance(path, str) and is_secret(path):
                found = (tool, os.path.basename(path))
        elif tool == "Bash":
            command = tool_input.get("command")
            if isinstance(command, str):
                cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
                found = secret_in_command(command, cwd)
    except Exception:  # noqa: BLE001 — fail open on a parse error (see module doc)
        return 0
    if found:
        what, name = found
        sys.stderr.write(
            "Memory Kit secrets guard: %s on `%s` blocked — a secret file's contents must not enter the "
            "transcript. Load it into a process instead (`source`, `set -a; . ./.env; set +a`) or move it "
            "whole (`cp`); if the user really wants it shown, they run it themselves. Set "
            "CMK_SECRETS_GUARD=off to disable.\n" % (what, name)
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
