"""Shell-command parser for the Memory Kit git guard (`hooks/guard-git.py`).

Ported from a project-level guard (2026-09-26) with one policy change: a directory the shell would
compute (`cd "$(mktemp -d)"`, `git -C $(pwd)`) resolves to None instead of raising — the dangers the
guard looks for are flag-shaped, so an unknown directory must never make it fail open.

`git_calls(command, cwd)` lexes a Bash command like a shell and returns every real git invocation:
    {"dir": abs dir after cd / -C, or None when computed at run time,
     "gopts": [-c/--git-dir/--work-tree opts], "env": {VAR: value},
     "sub": subcommand or None, "args": [Word, ...] after the subcommand}
Handled: quotes (text inside quotes is never a command), `&&`/`||`/`;`/`|`/`&`/newlines, comments,
heredocs (bodies skipped), `$(...)`/backticks/`<(...)` (recursed), redirections, `cd`/`pushd`,
leading `VAR=x`, `command`, `env`, `exec`, `nohup`, `time`, `builtin`, `timeout`, `nice`, `sudo`,
`xargs` (each after its own options), `eval`, `sh|bash|zsh|dash|ksh -c '<script>'`,
`if/then/do/!/{` prefixes.
Raises ValueError only on a lexing problem (unterminated quote / substitution) or nesting deeper
than MAX_DEPTH — the caller decides the failure policy.
Known gaps (not parsed, by design): git aliases, shell functions, commands inside script files,
a subcommand the shell computes (`git $(echo push) -f`).
Python 3.9+, stdlib only.
"""

from __future__ import annotations

import os
import re

ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELLS = ("sh", "bash", "zsh", "dash", "ksh")
KEYWORDS = ("if", "then", "else", "elif", "do", "while", "until", "!", "{")
# Wrappers that run their argv as a command: name -> (options that take a SEPARATE value,
# positionals to skip before the command). Option clusters and `--opt=value` are one word already.
WRAPPERS = {
    "exec": (("-a",), 0),
    "nohup": ((), 0),
    "time": (("-f", "-o", "--format", "--output"), 0),
    "builtin": ((), 0),
    "timeout": (("-s", "--signal", "-k", "--kill-after"), 1),  # then DURATION
    "nice": (("-n", "--adjustment"), 0),
    "sudo": (
        ("-u", "--user", "-g", "--group", "-C", "--close-from", "-D", "--chdir", "-h", "--host",
         "-p", "--prompt", "-r", "--role", "-t", "--type", "-T", "--command-timeout",
         "-U", "--other-user", "-R", "--chroot"),
        0,
    ),
    "xargs": (
        ("-I", "-L", "-n", "-P", "-s", "-E", "-a", "-d", "--replace", "--max-lines", "--max-args",
         "--max-procs", "--max-chars", "--eof", "--arg-file", "--delimiter", "--process-slot-var"),
        0,
    ),
}
MAX_DEPTH = 8
SUBST = "\x00"  # stands in for a $(...) / backtick result inside a word


class Word(str):
    dynamic = False  # True when the shell would expand part of it ($VAR, $(...), `...`)


# --------------------------------------------------------------------------- lexer


def lex(s):
    items, _ = _parse(s, 0, False)
    return items


def _parse(s, i, in_subst):
    """Items: ('cmd', [Word]) | ('sub', items). Stops at an unmatched ')' when in_subst."""
    n = len(s)
    items, words, subs, heredocs = [], [], [], []
    st = {"buf": [], "in_word": False, "dyn": False, "redirect": None}
    depth = 0

    def end_word():
        if not st["in_word"]:
            return
        w = Word("".join(st["buf"]))
        w.dynamic = st["dyn"]
        st.update(buf=[], in_word=False, dyn=False)
        red, st["redirect"] = st["redirect"], None
        if red == "skip":
            return
        if red == "heredoc":
            heredocs.append(str(w))
            return
        words.append(w)

    def end_cmd():
        end_word()
        for sb in subs:
            items.append(("sub", sb))
        if words:
            items.append(("cmd", list(words)))
        del words[:]
        del subs[:]

    def add(text, dyn=False):
        st["buf"].append(text)
        st["in_word"] = True
        if dyn:
            st["dyn"] = True

    def is_var_start(k):
        return k < n and (s[k].isalnum() or s[k] in "_{@*#?$!-")

    while i < n:
        c = s[i]
        if c == "\\":
            if i + 1 < n and s[i + 1] != "\n":
                add(s[i + 1])
            i += 2
            continue
        if c == "'":
            j = s.find("'", i + 1)
            if j < 0:
                raise ValueError("unterminated single quote")
            add(s[i + 1 : j])
            i = j + 1
            continue
        if c == '"':
            add("")
            i += 1
            while True:
                if i >= n:
                    raise ValueError("unterminated double quote")
                d = s[i]
                if d == '"':
                    i += 1
                    break
                if d == "\\" and i + 1 < n:
                    if s[i + 1] != "\n":
                        add(s[i + 1] if s[i + 1] in '$`"\\' else s[i : i + 2])
                    i += 2
                elif d == "$" and i + 1 < n and s[i + 1] == "(":
                    sub_items, i = _parse(s, i + 2, True)
                    subs.append(sub_items)
                    add(SUBST, True)
                elif d == "`":
                    sub_items, i = _backtick(s, i + 1)
                    subs.append(sub_items)
                    add(SUBST, True)
                else:
                    add(d, d == "$" and is_var_start(i + 1))
                    i += 1
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "(":
            sub_items, i = _parse(s, i + 2, True)
            subs.append(sub_items)
            add(SUBST, True)
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "'":
            j = i + 2
            while j < n and s[j] != "'":
                j += 2 if s[j] == "\\" else 1
            if j >= n:
                raise ValueError("unterminated $'...' quote")
            add(s[i + 2 : j])
            i = j + 1
            continue
        if c == "`":
            sub_items, i = _backtick(s, i + 1)
            subs.append(sub_items)
            add(SUBST, True)
            continue
        if c in " \t\r":
            end_word()
            i += 1
            continue
        if c == "#" and not st["in_word"]:
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "\n":
            end_cmd()
            i += 1
            for delim in heredocs:
                while i < n:
                    j = s.find("\n", i)
                    line = s[i:] if j < 0 else s[i:j]
                    i = n if j < 0 else j + 1
                    if line.strip() == delim:
                        break
            del heredocs[:]
            continue
        if c in ";&|":
            end_cmd()
            i += 1
            continue
        if c == "(":
            end_cmd()
            depth += 1
            i += 1
            continue
        if c == ")":
            end_cmd()
            i += 1
            if depth == 0:
                if in_subst:
                    return items, i
                continue
            depth -= 1
            continue
        if c in "<>":
            if st["in_word"] and not st["dyn"] and "".join(st["buf"]).isdigit():
                st.update(buf=[], in_word=False)  # `2>` — the digits are an fd, not a word
            else:
                end_word()
            j = i + 1
            while j < n and s[j] in "<>&|":
                j += 1
            op = s[i:j]
            if j < n and s[j] == "(" and op in ("<", ">"):
                sub_items, i = _parse(s, j + 1, True)  # process substitution
                subs.append(sub_items)
                continue
            if op == "<<" and j < n and s[j] == "-":
                j += 1
            st["redirect"] = "heredoc" if op == "<<" else "skip"
            i = j
            continue
        add(c, c == "$" and is_var_start(i + 1))
        i += 1

    end_cmd()
    if in_subst:
        raise ValueError("unterminated $(")
    return items, i


def _backtick(s, i):
    body = []
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            body.append(s[i + 1])
            i += 2
            continue
        if s[i] == "`":
            return lex("".join(body)), i + 1
        body.append(s[i])
        i += 1
    raise ValueError("unterminated backtick")


# --------------------------------------------------------------------------- command walk


def _resolve_dir(base, p):
    """The directory after `cd p` from `base`; None when either is computed at run time."""
    if base is None or SUBST in p:
        return None
    p = os.path.expanduser(os.path.expandvars(p))
    return os.path.normpath(os.path.join(base, p))


def walk(items, state, out, depth=0):
    if depth > MAX_DEPTH:
        raise ValueError("command nesting deeper than %d" % MAX_DEPTH)
    for kind, val in items:
        if kind == "sub":
            walk(val, dict(state), out, depth + 1)
        else:
            _simple(list(val), state, out, depth)


def _simple(words, state, out, depth):
    env = {}
    cwd = state["cwd"]
    while words:
        w = words[0]
        base = os.path.basename(w)
        if ASSIGN_RE.match(w):
            k, v = w.split("=", 1)
            env[k] = v
            words.pop(0)
        elif w in KEYWORDS:
            words.pop(0)
        elif base == "command":
            words.pop(0)
            while words and words[0].startswith("-"):
                opt = words.pop(0)
                if "v" in opt.lower():
                    return  # `command -v` only looks the name up
        elif base == "env":
            words.pop(0)
            while words and words[0].startswith("-"):
                opt = words.pop(0)
                if opt == "--":
                    break
                if opt in ("-u", "-P") and words:
                    words.pop(0)
                elif opt in ("-C", "--chdir") and words:
                    cwd = _resolve_dir(cwd, words.pop(0))
                elif opt.startswith("--chdir="):
                    cwd = _resolve_dir(cwd, opt.split("=", 1)[1])
                elif opt == "-S" and words:
                    head = [x for kind, cmd in lex(words.pop(0)) if kind == "cmd" for x in cmd]
                    words = head + words
        elif base in WRAPPERS:
            value_opts, skip = WRAPPERS[base]
            words.pop(0)
            while words and words[0].startswith("-") and len(words[0]) > 1:
                opt = words.pop(0)
                if opt == "--":
                    break
                if opt in value_opts and words:
                    words.pop(0)
            for _ in range(skip):
                if words:
                    words.pop(0)
        else:
            break
    if not words:
        return
    base = os.path.basename(words[0])
    if base in ("cd", "pushd"):
        args = [a for a in words[1:] if not (a.startswith("-") and a != "-")]
        if not args:
            state["cwd"] = os.path.expanduser("~")
        elif args[0] != "-":
            state["cwd"] = _resolve_dir(state["cwd"], args[0])
        return
    if base == "eval":
        walk(lex(" ".join(words[1:])), state, out, depth + 1)
        return
    if base in SHELLS:
        script = _shell_c_script(words[1:])
        if script is not None:
            walk(lex(script), {"cwd": cwd}, out, depth + 1)
        return
    if base == "git":
        out.append(_git_call(words[1:], cwd, env))


def _shell_c_script(args):
    has_c = False
    k = 0
    while k < len(args):
        a = args[k]
        if a in ("-o", "+o", "-O", "+O"):
            k += 2
            continue
        if a == "--":
            k += 1
            break
        if (a.startswith("-") or a.startswith("+")) and len(a) > 1 and not a.startswith("--"):
            has_c = has_c or "c" in a[1:]
            k += 1
            continue
        if a.startswith("--"):
            k += 1
            continue
        break
    if has_c and k < len(args):
        return args[k]
    return None


def _git_call(args, cwd, env):
    gdir, gopts, k = cwd, [], 0
    while k < len(args):
        a = args[k]
        if a == "-C" and k + 1 < len(args):
            gdir = _resolve_dir(gdir, args[k + 1])
            k += 2
        elif a == "-c" and k + 1 < len(args):
            gopts += ["-c", str(args[k + 1])]
            k += 2
        elif a in ("--git-dir", "--work-tree") and k + 1 < len(args):
            gopts.append("%s=%s" % (a, args[k + 1]))
            k += 2
        elif a.startswith("--git-dir=") or a.startswith("--work-tree="):
            gopts.append(str(a))
            k += 1
        elif a in ("--namespace", "--config-env", "--super-prefix") and k + 1 < len(args):
            k += 2
        elif a.startswith("-"):
            k += 1
        else:
            break
    sub = args[k] if k < len(args) else None
    return {"dir": gdir, "gopts": gopts, "env": env, "sub": sub, "args": list(args[k + 1 :])}


def git_calls(command, cwd):
    out = []
    walk(lex(command), {"cwd": cwd}, out)
    return out
