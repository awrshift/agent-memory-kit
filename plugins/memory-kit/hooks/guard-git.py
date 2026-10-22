#!/usr/bin/env python3
"""PreToolUse(Bash) — the Memory Kit git guard: blocks destructive git invocations, and only real ones.

Why a hook and not a permission rule: a permission rule is a PREFIX (`Bash(git push --force:*)`), so
`git push origin feat --force`, `git -C x push -f`, `cd dir && git push +main` all walk past it. The
danger is a flag anywhere in a real git argv — that takes a parser, not a prefix.

Contract: JSON on stdin ({"tool_name", "tool_input": {"command"}, "cwd"}); exit 0 = no opinion,
exit 2 + reason on stderr = block. Python 3.9+, stdlib only; never spawns a process.

Blocked (a real git argv found by `lib/cmdparse.py`; text inside quotes, heredoc bodies and
arguments of echo/grep/... never counts):
  push      --force / -f in any short cluster / a `+refspec` / --mirror
            (--force-with-lease and --force-if-includes alone are allowed; --force next to a
            lease still blocks)
  reset     --hard
  clean     -f in any short cluster (-f, -fd, -fdx) or --force
  branch    -D in any short cluster, or delete + force (-d -f, --delete --force)
  checkout  a whole-tree pathspec (`.`, `./`, `:/`), e.g. `checkout .`, `checkout -- .`
  restore   a whole-tree pathspec touching the worktree (`restore .`, `--staged --worktree .`);
            `restore --staged .` only resets the index and is allowed
Opt-out: CMK_GIT_GUARD=off in the environment.
Failure policy (7.3): fail OPEN on a lexing error (an unbalanced quote is also a command the shell
refuses to run) and on a payload that is not a tool call. A directory computed at run time is NOT a
parse error — it resolves to None. Any OTHER exception — a bug, a missing `lib/cmdparse.py`, nesting
past the parser's depth (a command the shell would run) — prints `permissionDecision: "ask"` naming the
guard and the error, exit 0. hooks.json sets `"onFailure": "block"` and first proves `python3` RUNS
(3.9+; the macOS stub that exists and exits 1 is a no-op, not a block).
Known gaps: git aliases, shell functions, commands inside script files.
"""

from __future__ import annotations

import json
import os
import sys

sys.dont_write_bytecode = True  # the plugin directory is not ours to litter with __pycache__

WATCHED = ("push", "reset", "clean", "branch", "checkout", "restore")
WHOLE_TREE = (".", "./", ":/")
PUSH_VALUE_OPTS = ("-o", "--push-option", "--repo", "--receive-pack", "--exec")
LEASE = "use --force-with-lease=<branch>:<expected sha>"


def _split(args, value_opts=()):
    """(long option names, short option letters, positionals) — `--` ends the options."""
    longs, shorts, positional = set(), set(), []
    k = 0
    while k < len(args):
        a = args[k]
        if a == "--":
            positional += args[k + 1 :]
            break
        if a in value_opts:
            k += 2
            continue
        if a.startswith("--"):
            longs.add(a[2:].split("=", 1)[0])
        elif a.startswith("-") and len(a) > 1:
            shorts.update(a[1:])
        else:
            positional.append(a)
        k += 1
    return longs, shorts, positional


def _danger(sub, args):
    """(operation, reason) or None."""
    if sub == "push":
        longs, shorts, positional = _split(args, PUSH_VALUE_OPTS)
        if "force" in longs or "f" in shorts:
            return "git push --force", "a force push rewrites the remote branch; " + LEASE
        if "mirror" in longs:
            return "git push --mirror", "a mirror push force-updates and deletes every remote ref"
        forced = [p for p in positional[1:] if p.startswith("+")]
        if forced:
            return "git push +refspec", "a `+` refspec (%s) is a force push; %s" % (", ".join(forced), LEASE)
    elif sub == "reset":
        longs, _, _ = _split(args)
        if "hard" in longs:
            return "git reset --hard", "it discards uncommitted work"
    elif sub == "clean":
        longs, shorts, _ = _split(args, ("-e", "--exclude"))
        if "f" in shorts or "force" in longs:
            return "git clean -f", "it deletes untracked files"
    elif sub == "branch":
        longs, shorts, _ = _split(args)
        delete = "d" in shorts or "delete" in longs
        force = "f" in shorts or "force" in longs
        if "D" in shorts or (delete and force):
            return "git branch -D", "it force-deletes a branch (unmerged commits are lost)"
    elif sub == "checkout":
        _, _, positional = _split(args, ("-b", "-B", "--orphan"))
        if any(p in WHOLE_TREE for p in positional):
            return "git checkout .", "it discards every uncommitted change in the tree"
    elif sub == "restore":
        longs, shorts, positional = _split(args, ("-s", "--source"))
        staged_only = ("S" in shorts or "staged" in longs) and not ("W" in shorts or "worktree" in longs)
        if any(p in WHOLE_TREE for p in positional) and not staged_only:
            return "git restore .", "it discards every uncommitted change in the tree"
    return None


def check(command, cwd):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
    import cmdparse

    for call in cmdparse.git_calls(command, cwd):
        if call["sub"] in WATCHED:
            found = _danger(call["sub"], call["args"])
            if found:
                return found
    return None


def verdict(raw):
    """(operation, reason) when blocked, None when allowed. Raises on an internal error."""
    if "git" not in raw:  # fast path: most Bash commands never mention git
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None  # not a tool call we can read (see module doc)
    if not isinstance(data, dict) or not isinstance(data.get("tool_input") or {}, dict):
        return None
    if data.get("tool_name", "Bash") != "Bash":
        return None
    command = (data.get("tool_input") or {}).get("command")
    if not isinstance(command, str) or "git" not in command:
        return None
    if not any(w in command for w in WATCHED):
        return None
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        return check(command, cwd)
    except ValueError as exc:
        if type(exc).__name__ == "NestingError":
            raise
        return None  # a lexing error: the shell refuses this command too


def ask(exc):
    reason = (
        "Memory Kit git guard failed internally (%s: %s) and could not check this call — approve it only "
        "if it is not a destructive git command. Set CMK_GIT_GUARD=off to disable the guard."
        % (type(exc).__name__, exc)
    )
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                      "permissionDecisionReason": reason}}, sys.stdout)
    sys.stdout.write("\n")


def main():
    if os.environ.get("CMK_GIT_GUARD", "").lower() == "off":
        return 0
    try:
        found = verdict(sys.stdin.read())
    except Exception as exc:  # noqa: BLE001 — an internal error asks the user; never a silent pass
        ask(exc)
        return 0
    if found:
        op, reason = found
        sys.stderr.write(
            "Memory Kit git guard: `%s` blocked — %s. If the user really wants this, they run it "
            "themselves. Set CMK_GIT_GUARD=off to disable.\n" % (op, reason)
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
