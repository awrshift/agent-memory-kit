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
                        an APPEND to a secret file is allowed only on a positive signal (7.3, an
                        allowlist): every secret-named redirection is a plain stdout append (`>>`, `1>>`,
                        `&>>`), every command in the line (`$(…)` and backticks included) is `echo`,
                        `printf`, or `cat` with no file argument, a heredoc delimiter is quoted (`<<'EOF'`:
                        the body is not expanded), and no redirection reads a file (`<`, `<&`, `<>`).
                        Why not a list of bad shapes: on Linux reopening an fd path reads the appended file
                        back (`cp /proc/self/fd/1 x >> .env`), and its spellings are open-ended
                        (`/proc/<pid>/task/<tid>/fd/1`, a path inside a heredoc or an interpreter's stdin);
                        a word after an inline-script option (`-e`, `-c`, `-E`, `-p`, `-r`, `--eval`,
                        `--print`, `--command`, a short cluster ending in c/e) and every word of an
                        interpreter (node, python, perl, ruby, php, deno, bun, …) is also split into
                        path-like tokens, so `node -e "fs.readFileSync('.env')"` counts.
Allowed commands whatever their arguments: `source` / `.` (loading into a process), `cp` / `ln` /
`mv` (moving the file whole — an executor copying the env into its worktree), `ls`, `test` / `[` /
`[[`, `git`, `rm`.
Opt-out: CMK_SECRETS_GUARD=off in the environment.
Failure policy (7.3): fail OPEN on a lexing error (an unbalanced quote is also a command the shell refuses)
and on a payload that is not a tool call (not JSON, `tool_input` not an object). Any OTHER exception —
a bug, a missing `lib/cmdparse.py`, nesting past the parser's depth (a command the shell would run) —
prints `permissionDecision: "ask"` naming the guard and the error, exit 0: the user decides, nothing
passes silently. hooks.json sets `"onFailure": "block"` (a crash, timeout or invalid output blocks the
call) and checks `python3` exists first, so a machine without it is an explicit no-op, not a blocked session.
Known gaps: globs (`cat .e*`), heredoc bodies fed to an interpreter (`python3 - <<EOF`), script
files, a copy read afterwards (`cp .env x && cat x`), tools outside the matcher (Grep, NotebookEdit),
an fd path the shell computes (`/dev/f$X/1`) or reaches through a symlink made earlier.
Search patterns are not paths: the pattern word of grep/egrep/fgrep/rg/ag/ack (`grep -rn '.env' src`, `-e .env`) and
the value of find's -name/-path/-regex are skipped. `grep x .env` (the FILE operand) is still blocked.
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
# The only appends that write without a way to read back: stdout alone, or stdout + stderr.
PLAIN_APPENDS = {">>", "1>>", "&>>"}
# The commands a secret append may come with — they print their arguments or stdin and read no file.
APPEND_WRITERS = {"echo", "printf"}


def is_secret(path):
    return bool(SECRET_RE.match(os.path.basename(str(path)).lower()))


def _script_word(prev):
    if prev in SCRIPT_OPTS:
        return True
    return len(prev) > 1 and prev[0] == "-" and prev[1] != "-" and prev[-1] in "ce"


SEARCHERS = {"grep", "egrep", "fgrep", "rg", "ag", "ack", "git-grep"}
FIND_PATTERN_OPTS = {"-name", "-iname", "-path", "-ipath", "-wholename", "-iwholename", "-regex", "-iregex"}


def _pattern_words(name, argv):
    """Indices of words that are search PATTERNS, not paths: `grep -rn '.env' src` searches FOR the text,
    `find . -name .env` matches names. A secret name there reads nothing (7.2.0: these were false positives)."""
    skip = set()
    if name in SEARCHERS:
        pattern_given = False
        k = 1
        while k < len(argv):
            w = argv[k]
            if w in ("-e", "--regexp", "-f", "--file"):
                if w in ("-e", "--regexp"):
                    skip.add(k + 1)
                    pattern_given = True
                k += 2
                continue
            if w.startswith("--regexp="):
                pattern_given = True
            elif not w.startswith("-") and not pattern_given:
                skip.add(k)
                pattern_given = True
            k += 1
    elif name == "find":
        for k, w in enumerate(argv[:-1]):
            if w in FIND_PATTERN_OPTS:
                skip.add(k + 1)
    return skip


def append_blocker(calls):
    """What keeps a secret append from its exemption, or None when the whole line is on the allowlist."""
    for call in calls:
        for target in call.get("redirects", ()):
            op = getattr(target, "op", "")
            if "<" in op:
                return "the input redirection `%s %s`" % (op, target)
        for delim in call.get("heredocs", ()):
            if not getattr(delim, "quoted", False):
                return "an unquoted heredoc `<<%s` (its body expands `$(…)`)" % delim
        name = call["name"]
        if name is None:
            continue
        argv = [str(w) for w in call["argv"]]
        if argv[0] in APPEND_WRITERS:
            continue
        if argv[0] == "cat" and all(w.startswith("-") for w in argv[1:]):
            continue
        return "`%s`" % " ".join(argv)[:80]
    return None


def load_cmdparse():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
    import cmdparse

    return cmdparse


def secret_in_command(command, cwd):
    """(what, secret word) for the first blocked use, or None."""
    cmdparse = load_cmdparse()
    calls = cmdparse.commands(command, cwd)
    appended = None
    for call in calls:
        for target in call.get("redirects", ()):
            if not is_secret(target):
                continue
            op = getattr(target, "op", "")
            # `>> .env` appends: nothing of the file comes back into the transcript (owner 2026-10-20,
            # the agent keeps the project's env up to date). `>`, `<`, `&>` and `2>>` stay blocked.
            if op not in PLAIN_APPENDS:
                return "redirection `%s`" % op, str(target)
            appended = appended or str(target)
        name = call["name"]
        if name is None or name in EXEMPT:
            continue
        argv = [str(w) for w in call["argv"]]
        interpreter = bool(INTERPRETER_RE.match(name))
        skip = _pattern_words(name, argv)
        for k, word in enumerate(argv):
            if k in skip:
                continue
            if is_secret(word):
                return name, word
            if interpreter or (k > 0 and _script_word(argv[k - 1])):
                for token in NOT_PATH_RE.split(word):
                    if token and is_secret(token):
                        return name, token
    if appended:
        blocker = append_blocker(calls)
        if blocker:
            return "an append beside %s" % blocker, appended
    return None


def check(raw):
    """(what, name) when the call is blocked, None when allowed. Raises on an internal error."""
    low = raw.lower()
    if not any(marker in low for marker in FAST_PATH):
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None  # not a tool call we can read (see module doc)
    if not isinstance(data, dict) or not isinstance(data.get("tool_input") or {}, dict):
        return None
    tool = data.get("tool_name")
    tool_input = data.get("tool_input") or {}
    if tool in ("Read", "Edit", "Write"):
        path = tool_input.get("file_path")
        if isinstance(path, str) and is_secret(path):
            return tool, os.path.basename(path)
    elif tool == "Bash":
        command = tool_input.get("command")
        if isinstance(command, str):
            cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
            try:
                return secret_in_command(command, cwd)
            except ValueError as exc:
                if type(exc).__name__ == "NestingError":
                    raise
                return None  # a lexing error: the shell refuses this command too
    return None


def ask(exc):
    reason = (
        "Memory Kit secrets guard failed internally (%s: %s) and could not check this call — "
        "approve it only if it does not read a secret file. Set CMK_SECRETS_GUARD=off to disable the guard."
        % (type(exc).__name__, exc)
    )
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                      "permissionDecisionReason": reason}}, sys.stdout)
    sys.stdout.write("\n")


def main():
    if os.environ.get("CMK_SECRETS_GUARD", "").lower() == "off":
        return 0
    try:
        found = check(sys.stdin.read())
    except Exception as exc:  # noqa: BLE001 — an internal error asks the user; never a silent pass
        ask(exc)
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
