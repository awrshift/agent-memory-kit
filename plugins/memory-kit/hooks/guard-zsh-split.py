#!/usr/bin/env python3
"""PreToolUse(Bash) — the Memory Kit zsh guard: an unquoted scalar `$var` is NOT word-split in zsh.

When the Bash tool runs zsh, `a="x y"; set -- $a` gives ONE argument «x y» (bash gives two), and
`f=$(git ls-files); for x in $f` loops ONCE over the whole list. The command then "succeeds" with
empty or wrong arguments. A prose warning did not stop it in the project this guard comes from, so it
is a hook: it blocks the command before it runs, and the model retries with the right form.

Only when the Bash tool's shell is zsh. Claude Code picks that shell as documented for
`CLAUDE_CODE_SHELL` (code.claude.com/docs/en/env-vars, read 2026-10-22): `$CLAUDE_CODE_SHELL` when it is
an executable `bash`/`zsh`, else `$SHELL` when it is, else the first zsh, then bash, on PATH or in a
standard location. Not zsh → no output, exit 0.

Positive signal only (a block costs one retry):
  a variable THIS command makes a scalar that holds several words —
    `NAME="a b"` / `NAME='a b'` (whitespace in the value, outside `$(…)`), `NAME=$(…)` / `NAME=`…``,
    or a `for NAME in …` loop over a quoted item with whitespace —
  then uses UNQUOTED where splitting is expected:
    a `for … in` list · `set [--] …` · and, for a value with whitespace outside `$(…)`, the command
    position or any argument.
  Assignments in one command run left to right: `x="a b" y=$(printf %s $x)` — the substitution sees x.
  Not flagged: quoted uses ("$NAME"), `${=NAME}` / `$=NAME`, arrays `NAME=(…)` and `${NAME[@]}`,
  `$NAME[…]`, variables this command does not assign (shell state does not persist between Bash calls),
  a prefix assignment `NAME=v cmd` (it sets NAME for cmd only: `MSG="a b" git commit; ls $MSG` is not it),
  heredoc bodies, single-quoted text, arithmetic `$((…))`, the value of an assignment (`b=$a` never
  splits), a redirection target (one word in zsh; bash refuses it as an ambiguous redirect), words
  passed to echo / print / eval / [ / [[ / test (joining them changes nothing).
  A `$(…)` variable is flagged only in a `for` list or `set` (`d=$(pwd); cd $d` and `P=$(which psql); $P`
  are one word and work).
Second class — zsh history modifiers on an unbraced `$NAME:`: `git show $U:src/x.ts` runs `:s`
  (substitution), `$U:qa/x` runs `:q`, `$U:test` runs `:t` — the path is eaten or the command fails with
  «bad substitution». Flagged: `$NAME:` + a modifier letter zsh 5.9 applies unbraced (a c e h l q r s t u
  A P Q, or `gs` / `g&`) + a word character right after it, unquoted or in double quotes. Not flagged:
  `${NAME}:…`, a modifier followed by `:`, `/`, `.`, a space or a quote (`$f:t:r`, `$f:h/x`, `$f:r.bak`),
  a letter zsh leaves literal (`$U:docs/x`), single quotes, `\\$`.

Override: `# zsh-split-ok` anywhere in the command. Opt-out: CMK_ZSH_GUARD=off in the environment.
Runs in every repo, adopted or not (like the git guard): it protects the user's commands, not memory.

Contract: JSON on stdin ({"tool_name", "tool_input": {"command"}}); exit 0 = no opinion; exit 2 + reason
on stderr = block. Parser: `lib/cmdparse.py` (`lex`). Failure policy: a lexing problem (an unbalanced
quote or substitution) is no opinion — the shell refuses that command too; nesting deeper than
cmdparse.MAX_DEPTH (`cmdparse.NestingError`, a command the shell WOULD run) and any other internal error
answer `permissionDecision: "ask"` naming the guard and the error, exit 0 (7.3 r2).
Probed live on zsh 5.9 (2026-10-22): `set -- $a` → 1 argument, `${=a}` / `$=a` → 2; `$U:<l>x` eats `:<l>`
for exactly the letters above and leaves b d f literal; `> $out` writes one file `a b.log`.
Known gap: a scalar copied from another (`b=$a`) is not tracked. Python 3.9+, stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True  # the plugin directory is not ours to litter with __pycache__
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import cmdparse
except Exception as _error:  # noqa: BLE001 — reported as an `ask` by main(), never a silent pass
    cmdparse = None
    IMPORT_ERROR = _error

GUARD = "Memory Kit zsh guard"
OVERRIDE = "# zsh-split-ok"
NAME = r"[A-Za-z_][A-Za-z0-9_]*"
USE = re.compile(r"\$(?:\{(" + NAME + r")(?=[}:])|(" + NAME + r"))")
MODIFIER = re.compile(r"\$(" + NAME + r"):(g[s&]|[acehlqrstuAPQ])(?=[A-Za-z0-9_])")
ASSIGN = re.compile(r"(" + NAME + r")=")
LEADING = ("if", "then", "else", "elif", "do", "while", "until", "!", "{")
DECLARE = ("export", "local", "typeset", "declare", "readonly", "integer", "float")
NO_SPLIT = ("echo", "print", "eval", "[", "[[", "test")  # joining the words changes nothing here
SPLITTING = ("multi", "subst")
STANDARD_DIRS = ("/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin")


# --------------------------------------------------------------------------- which shell


def _shell_of(path):
    """'bash' / 'zsh' when `path` is an executable bash or zsh, else None."""
    if not path:
        return None
    base = os.path.basename(path)
    if base in ("bash", "zsh") and os.path.isfile(path) and os.access(path, os.X_OK):
        return base
    return None


def bash_tool_shell(env=None):
    """The shell Claude Code's Bash tool runs, by its documented detection order."""
    env = os.environ if env is None else env
    for var in ("CLAUDE_CODE_SHELL", "SHELL"):
        found = _shell_of(env.get(var))
        if found:
            return found
    for name in ("zsh", "bash"):
        if shutil.which(name, path=env.get("PATH")):
            return name
        if any(_shell_of(os.path.join(d, name)) for d in STANDARD_DIRS):
            return name
    return None


# --------------------------------------------------------------------------- the check


def _unquoted(word, k, n=1):
    return word.quoting[k : k + n] == "u" * n


def _assignment(word):
    """(name, kind) when `word` is a shell assignment, else None. kind: array | multi | subst | single."""
    m = ASSIGN.match(word)
    if not m or not _unquoted(word, 0, m.end()):
        return None
    value = word[m.end() :]
    if word.array:
        kind = "array"
    elif any(ch.isspace() for ch in value):  # whitespace inside $(…) lives in the sub item, not here
        kind = "multi"
    elif cmdparse.SUBST in value:
        kind = "subst"
    else:
        kind = "single"
    return m.group(1), kind


def _modifiers(word, out):
    for m in MODIFIER.finditer(word):
        if word.quoting[m.start()] in "ud":
            out.append((m.group(1), "modifier", m.group(2)))


def _uses(word, kinds):
    """(name, kind) for every unquoted `$NAME` / `${NAME}` whose value this command made multi-word."""
    for m in USE.finditer(word):
        if word.quoting[m.start()] != "u":
            continue
        name = m.group(1) or m.group(2)
        if m.group(2) and word[m.end() : m.end() + 1] == "[":
            continue  # $NAME[…] subscript
        if kinds.get(name) in SPLITTING:
            yield name, kinds[name]


def _subs(pending, kinds, mods, hits, depth):
    for kind, val in pending:
        if kind == "sub":  # arithmetic: no word splitting, no history modifiers
            _walk(val, kinds, mods, hits, depth + 1)


def _command(words, kinds, mods, hits, pending, depth):
    """One simple command; `pending` = its substitutions, in source order (the lexer emits them first)."""
    for w in words:
        _modifiers(w, mods)
    k = 0
    while k < len(words) and words[k] in LEADING and _unquoted(words[k], 0, len(words[k])):
        k += 1
    first = k
    while k < len(words) and _assignment(words[k]):
        k += 1
    if k == len(words):  # assignments only: they set shell variables, left to right
        matched = sum(words[i].count(cmdparse.SUBST) for i in range(first, k)) == len(pending)
        if not matched:  # substitutions that cannot be matched to their words: walked first, as written
            _subs(pending, kinds, mods, hits, depth)
        queue = list(pending) if matched else []
        for i in range(first, k):
            n = words[i].count(cmdparse.SUBST) if matched else 0
            _subs(queue[:n], kinds, mods, hits, depth)  # a `$(…)` in a value sees the assignments before it
            del queue[:n]
            name, kind = _assignment(words[i])
            kinds[name] = kind
        return
    _subs(pending, kinds, mods, hits, depth)
    # `NAME=v cmd`: a prefix assignment sets NAME in cmd's environment only — not for later commands, and not
    # for this command's own words (they expand before it applies). Not tracked.
    argv0 = words[k]
    loop_var = None
    if argv0 == "for" and len(words) > k + 2 and words[k + 2] == "in" and re.fullmatch(NAME, words[k + 1]):
        loop_var = str(words[k + 1])
    for i in range(k, len(words)):
        w = words[i]
        if argv0 in DECLARE and i > k and _assignment(w):
            name, kind = _assignment(w)
            kinds[name] = kind
            continue
        if argv0 in NO_SPLIT:
            continue
        for name, kind in _uses(w, kinds):
            if loop_var is not None and i >= k + 3:
                where = "a `for … in` list"
            elif argv0 == "set":
                where = "`set`"
            elif kind == "multi" and i == k:
                where = "command position"
            elif kind == "multi":
                where = "an argument"
            else:
                continue
            hits.append((name, kind, where))
    if loop_var is not None:
        items = words[k + 3 :]
        quoted_ws = any(
            ch.isspace() and q != "u" for w in items for ch, q in zip(w, w.quoting)
        )  # `for x in "a b" "c d"` — each x holds several words
        kinds[loop_var] = "multi" if quoted_ws else "single"


def _walk(items, kinds, mods, hits, depth=0):
    if depth > cmdparse.MAX_DEPTH:
        raise cmdparse.NestingError("command nesting deeper than %d" % cmdparse.MAX_DEPTH)
    pending = []  # substitutions waiting for the command they belong to
    for kind, val in items:
        if kind in ("sub", "arith"):
            pending.append((kind, val))
        elif kind == "redir":
            _subs(pending, kinds, mods, hits, depth)
            pending = []
            for w in val:  # a redirection target is one word in zsh (bash: «ambiguous redirect»)
                _modifiers(w, mods)
        else:
            _command(val, kinds, mods, hits, pending, depth)
            pending = []
    _subs(pending, kinds, mods, hits, depth)


def check(command):
    """[(name, kind, where)] — the modifier hits when there are any, else the split hits."""
    if OVERRIDE in command or "$" not in command:
        return []
    kinds, mods, hits = {}, [], []
    _walk(cmdparse.lex(command), kinds, mods, hits)
    return mods or hits


def message(hits):
    name, kind, where = hits[0]
    if kind == "modifier":
        return (
            "%s: `$%s:%s…` — zsh reads `:%s` as a history modifier on `$%s` and eats the text after it "
            "(`git show $U:src/x` → «bad substitution»). Write `${%s}:…` or the value literally. If the "
            "modifier is intended, add `%s`." % (GUARD, name, where, where, name, name, OVERRIDE)
        )
    src = "a quoted string with spaces" if kind == "multi" else "a command substitution"
    return (
        "%s: `$%s` holds %s and is used unquoted in %s. The Bash tool runs zsh, and zsh does NOT word-split "
        "an unquoted scalar — the command would get ONE argument (or loop once). Write the words out, use an "
        "array `%s=(…)` with \"${%s[@]}\", or split explicitly with `${=%s}`. If one word is intended, quote "
        "it \"$%s\" or add `%s`." % (GUARD, name, src, where, name, name, name, name, OVERRIDE)
    )


def _ask(error):
    reason = (
        "%s hit an internal error (%s: %s), so this command was NOT checked for zsh word-splitting. "
        "Confirm to run it anyway. Set CMK_ZSH_GUARD=off to disable the guard." % (GUARD, type(error).__name__, error)
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(out) + "\n")
    return 0


def main():
    if os.environ.get("CMK_ZSH_GUARD", "").lower() == "off":
        return 0
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0  # not hook JSON: no opinion, like the git guard
    try:
        if cmdparse is None:
            raise IMPORT_ERROR
        if not isinstance(data, dict) or data.get("tool_name", "Bash") != "Bash":
            return 0
        command = (data.get("tool_input") or {}).get("command")
        if not isinstance(command, str) or "$" not in command:
            return 0
        if bash_tool_shell() != "zsh":
            return 0
        try:
            hits = check(command)
        except ValueError as error:
            if isinstance(error, cmdparse.NestingError):
                raise  # a command the shell WOULD run, not checked: ask (below), like the other guards
            return 0  # a lexing problem: the shell would refuse this command too
    except Exception as error:  # noqa: BLE001 — a guard bug must surface, never pass silently
        return _ask(error)
    if not hits:
        return 0
    sys.stderr.write(message(hits) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
