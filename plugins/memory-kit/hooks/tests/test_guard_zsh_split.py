#!/usr/bin/env python3
"""Tests for hooks/guard-zsh-split.py — run: python3 plugins/memory-kit/hooks/tests/test_guard_zsh_split.py

Hook-level cases feed hook JSON through the command string registered in hooks.json when it is wired
there, else through the planned entry (PLANNED) — `test_wired` then proves the wiring once it lands. The
`python3` that string names is pinned to the interpreter running these tests (a shim on PATH). The
shell the guard detects is a fake executable named `zsh` / `bash` in a temp dir, so the tests do not
depend on which shells this machine has.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(PLUGIN_ROOT, "hooks", "guard-zsh-split.py")
PLANNED = 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/guard-zsh-split.py"'


def wired_command():
    with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as fh:
        cfg = json.load(fh)
    for group in cfg["hooks"].get("PreToolUse", []):
        if group.get("matcher") == "Bash":
            for hook in group["hooks"]:
                if "guard-zsh-split.py" in hook["command"]:
                    return hook["command"]
    return None


WIRED = wired_command()
COMMAND = WIRED or PLANNED

TMP = tempfile.mkdtemp(prefix="cmk-zsh-")
PY_SHIM = os.path.join(TMP, "py")
SHELLS = os.path.join(TMP, "shells")
os.makedirs(PY_SHIM)
os.makedirs(SHELLS)
os.symlink(sys.executable, os.path.join(PY_SHIM, "python3"))
for _name in ("zsh", "bash"):
    _p = os.path.join(SHELLS, _name)
    with open(_p, "w") as _fh:
        _fh.write("#!/bin/sh\nexit 0\n")
    os.chmod(_p, 0o755)
FAKE_ZSH = os.path.join(SHELLS, "zsh")
FAKE_BASH = os.path.join(SHELLS, "bash")

BASE_ENV = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT, SHELL=FAKE_ZSH)
BASE_ENV["PATH"] = PY_SHIM + os.pathsep + os.environ["PATH"]
for _var in ("CMK_ZSH_GUARD", "CLAUDE_CODE_SHELL"):
    BASE_ENV.pop(_var, None)


def load_hook():
    sys.dont_write_bytecode = True  # no __pycache__ in the plugin's hooks/ directory
    spec = importlib.util.spec_from_file_location("guard_zsh_split", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = load_hook()

# The source hook's own self-test cases (avoid-content-backend `.claude/hooks/zsh-split-guard.py`,
# SELFTEST, 2026-10-17), project names replaced by neutral ones: (command, block?).
SOURCE_CASES = [
    ('for pair in "a b" "c d"; do set -- $pair; echo $1 $2; done', True),
    ('for r in "api 350" "web 224"; do set -- $r; gh pr view $2 --repo x/$1; done', True),
    ('f=$(git ls-files | head -3); echo "$f"; for x in $f; do grep -n X $x; done', True),
    ('P="docker exec db psql -U postgres"; $P -c "select 1"', True),
    ('a="x y"; printf "%s\\n" $a', True),
    ('for x in "1 a" "2 b"; do set -- ${=x}; echo $1; done', False),
    ("for f in $S/*.md; do python3 x.py $f; done", False),
    ('S=/tmp/x; for f in $S/*.md; do echo "$f"; done', False),
    ("d=$(pwd); cd $d && ls", False),
    ('a="x y"; echo "$a"', False),
    ("P=(a b c); for x in $P; do echo $x; done", False),
    ("python3 - <<'EOF'\na=\"x y\"\nprint($a)\nEOF", False),
    ("echo 'a=\"x y\"; set -- $a'", False),
    ("for x in a b c; do set -- $x; done", False),
    ("n=$(wc -l < f); echo $n", False),
    ("for b in x y; do mb=$(git merge-base $b main); for f in $(git diff --name-only $mb $b); do echo; done; done", False),
    ("for w in $(git worktree list | awk '{print $1}'); do git -C $w status; done", False),
    ('F="a.md b.md"; git add $(echo $F); git commit -m x -- $(echo $F)', False),
    ("K=\"$(pbpaste | tr -d '[:space:]')\"; curl -H \"k: $K\" x; [[ $K == AIza* ]] && echo ok", False),
    ('IK="audit-$(date +%s)"; curl -d $IK x', False),
    ('T="a b"; eval $T run', False),
    ('F="$(git diff --name-only) src/x.ts"; npx eslint $F', True),
    ('H="ctx/s-83-* ctx/s-84-*"; cat $H 2>/dev/null | grep -c x', True),
    ('for c in "pnpm depcruise" "pnpm test"; do bash $Q $c; done', True),
    ('a="x y"; for i in $a; do echo $i; done # zsh-split-ok', False),
    ('PSQL=$(which psql || echo /opt/x/psql); $PSQL -c "select 1"', False),
    ("U=abc; git show $U:src/a.ts | head", True),
    ('git show "$R:qa/x.md"', True),
    ("git show $B:test/y.ts", True),
    ("chown $USER:staff f", True),
    ("git show ${U}:src/a.ts", False),
    ("git show $U:docs/x.md", False),
    ("f=/a/b.c; echo $f:t:r $f:h/x; mv $f $f:r.bak", False),
    ("echo '$U:src'", False),
    ("curl http://$HOST:8080/x", False),
    ("echo \\$U:src", False),
    ("git show $U:src/a.ts # zsh-split-ok", False),
]

# A hand-built corpus of realistic commands (not taken from any transcript), labelled by hand with
# what zsh does: True = the command would NOT do what it says (block is right), False = it works.
CORPUS = [
    ("git status --short && git log --oneline -5", False),
    ('for f in src/*.ts; do echo "$f"; done', False),
    ('cd "$(git rev-parse --show-toplevel)" && ls', False),
    ('BRANCH=$(git branch --show-current); git push -u origin "$BRANCH"', False),
    ("BRANCH=$(git branch --show-current); git push -u origin $BRANCH", False),
    ('export PATH="$HOME/.local/bin:$PATH"; which uv', False),
    ("npm run build 2>&1 | tail -20", False),
    ('files=(src/a.ts src/b.ts); npx eslint "${files[@]}"', False),
    ("files=(src/a.ts src/b.ts); npx eslint $files", False),
    ('msg="fix: handle empty input"; git commit -m "$msg"', False),
    ('for i in {1..5}; do curl -s "http://localhost:8080/health"; done', False),
    ('count=$(grep -c TODO src/app.ts); echo "TODOs: $count"', False),
    ('if [ -n "$CI" ]; then echo ci; fi', False),
    ("DIR=/tmp/build; mkdir -p $DIR && cp dist/* $DIR/", False),
    ("python3 -c 'import sys; print(sys.version)'", False),
    ('docker compose -f "$COMPOSE_FILE" up -d', False),
    ('TOKEN=$(cat .token); curl -H "Authorization: Bearer $TOKEN" https://api.example.com/x', False),
    ("for pkg in react vue svelte; do npm view $pkg version; done", False),
    ("x=5; echo $((x * 2))", False),
    ("n=$(wc -l < data.csv); echo $(( n - 1 ))", False),
    ('nums="1 2"; total=$(( $nums )); echo "$total"', False),
    ("cat <<EOF > config.yml\nname: $NAME\nport: $PORT\nEOF", False),
    ("git log --format='%H %s' -3", False),
    ("jq -r '.items[] | \"\\(.id) \\(.name)\"' out.json", False),
    ("awk '{print $1, $2}' file.txt", False),
    ("find . -name '*.py' -exec grep -l \"import os\" {} +", False),
    ("ts=$(date +%Y%m%d); tar czf backup-$ts.tar.gz src/", False),
    ("PORT=8080 npm start", False),
    ("A=\"hello world\"; printf '%s\\n' \"$A\"", False),
    ('args=(-v --color); pytest "${args[@]}" tests/', False),
    ('opts="-la"; ls $opts', False),
    ('while read -r line; do echo "$line"; done < input.txt', False),
    ('for d in */; do (cd "$d" && git pull); done', False),
    ("sha=$(git rev-parse HEAD); git show $sha:README.md", False),
    ('git diff HEAD~1 -- "$(git ls-files | head -1)"', False),
    ('export NODE_OPTIONS="--max-old-space-size=4096 --trace-warnings"; npm test', False),
    ('cp "$SRC" "$DST"', False),
    ("ls -la ${HOME}/Downloads", False),
    ('echo "Done: $(date)"', False),
    ('name="my file.txt"; touch "$name"; ls -l "$name"', False),
    ('pid=$(lsof -ti :3000); [ -n "$pid" ] && echo "$pid"', False),
    ('for f in $(ls *.md); do wc -l "$f"; done', False),
    ('url="http://localhost:$PORT/api"; curl -s $url', False),
    ('curl -s "http://$HOST:8080/x"', False),
    ("f=report.tar.gz; echo $f:r", False),
    ("set -e; make build", False),
    ("set -- a b c; echo $#", False),
    ("export X=1 Y=2; env | grep -E '^(X|Y)='", False),
    ('a="x y"; b=$a; echo "$b"', False),
    ('out="build output.log"; make > $out 2>&1', False),
    ('list="a b"; arr=(${=list}); echo ${#arr}', False),
    ("parts=\"a b c\"; for p in $=parts; do echo $p; done", False),
    # realistic defects
    ('FILES="a.ts b.ts"; npx prettier --check $FILES', True),
    ("CMD=\"docker exec db psql -U postgres\"; $CMD -c 'select 1'", True),
    ("ids=$(gh pr list --json number -q '.[].number'); for id in $ids; do gh pr view $id; done", True),
    ('for row in "api 8080" "web 3000"; do set -- $row; echo "$1 on $2"; done', True),
    ("git show $BASE:src/main.ts", True),
    ("PGOPTS=\"-h localhost -p 5432\"; psql $PGOPTS -c 'select 1'", True),
    ('export FLAGS="--verbose --dry-run"; ./deploy.sh $FLAGS', True),
    ("ref=main; git diff $ref:test/a.ts", True),
]


def run_hook(command, env=None, tool="Bash", raw=None):
    payload = raw if raw is not None else json.dumps({"tool_name": tool, "tool_input": {"command": command}})
    return subprocess.run(COMMAND, shell=True, input=payload, capture_output=True, text=True, env=env or BASE_ENV)


class HookTest(unittest.TestCase):
    def assert_blocked(self, cmd):
        r = run_hook(cmd)
        self.assertEqual(r.returncode, 2, (cmd, r.stdout, r.stderr))
        self.assertIn("Memory Kit zsh guard", r.stderr)

    def assert_silent(self, cmd, env=None):
        r = run_hook(cmd, env=env)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""), cmd)

    def test_source_cases(self):
        for cmd, block in SOURCE_CASES:
            with self.subTest(cmd=cmd):
                (self.assert_blocked if block else self.assert_silent)(cmd)

    def test_message_says_how_to_split_in_zsh(self):
        r = run_hook('a="x y"; set -- $a')
        for part in ("`$a`", "set", 'a=(…)', '"${a[@]}"', "${=a}", '"$a"', "# zsh-split-ok"):
            self.assertIn(part, r.stderr)

    def test_modifier_message_says_brace_it(self):
        r = run_hook("git show $U:src/a.ts")
        self.assertEqual(r.returncode, 2)
        for part in ("history modifier", "${U}:", "`:s`"):
            self.assertIn(part, r.stderr)

    def test_inert_outside_zsh(self):
        cases = [c for c, block in SOURCE_CASES + CORPUS if block]
        bash_env = dict(BASE_ENV, SHELL=FAKE_BASH)
        override_env = dict(BASE_ENV, SHELL=FAKE_ZSH, CLAUDE_CODE_SHELL=FAKE_BASH)
        for env in (bash_env, override_env):
            for cmd in cases:
                with self.subTest(cmd=cmd, shell=env.get("CLAUDE_CODE_SHELL", env["SHELL"])):
                    self.assert_silent(cmd, env=env)

    def test_claude_code_shell_wins_over_shell(self):
        env = dict(BASE_ENV, SHELL=FAKE_BASH, CLAUDE_CODE_SHELL=FAKE_ZSH)
        self.assertEqual(run_hook('a="x y"; set -- $a', env=env).returncode, 2)

    def test_opt_out(self):
        self.assert_silent('a="x y"; set -- $a', env=dict(BASE_ENV, CMK_ZSH_GUARD="off"))

    def test_non_bash_tool(self):
        r = run_hook('a="x y"; set -- $a', tool="Read")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_garbage_stdin_is_no_opinion(self):
        for raw in ("", "not json", "[1, 2]", '{"tool_input": null}', '{"tool_input": {"command": 5}}'):
            with self.subTest(raw=raw):
                r = run_hook(None, raw=raw)
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_unbalanced_command_is_no_opinion(self):
        for cmd in ('a="x y"; set -- $a "unterminated', "a='x y'; set -- $a 'open", 'set -- $(echo "x y"'):
            with self.subTest(cmd=cmd):
                self.assert_silent(cmd)

    def assert_ask(self, r, *parts):
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn("Memory Kit zsh guard", out["permissionDecisionReason"])
        for part in parts:
            self.assertIn(part, out["permissionDecisionReason"])

    def test_internal_error_asks(self):
        # nesting past Python's recursion limit is an internal error of the parser, not a verdict
        r = run_hook("echo " + "$(" * 3000 + "x" + ")" * 3000)
        self.assert_ask(r, "RecursionError")

    def test_missing_parser_asks(self):
        alone = os.path.join(TMP, "alone", "hooks")
        os.makedirs(alone, exist_ok=True)
        shutil.copy(HOOK, alone)  # no lib/ next to it
        cmd = '"%s" "%s"' % (sys.executable, os.path.join(alone, "guard-zsh-split.py"))
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": 'a="x y"; set -- $a'}})
        r = subprocess.run(cmd, shell=True, input=payload, capture_output=True, text=True, env=BASE_ENV)
        self.assert_ask(r, "ModuleNotFoundError", "cmdparse")

    def test_worst_case_under_two_seconds(self):
        n = 100_000
        cases = {
            "unclosed double quote": ('a="x y"; set -- $a "' + "ab" * (n // 2), 0),
            "unclosed single quote": ("a='x y'; set -- $a '" + "ab" * (n // 2), 0),
            "$a repeated": ('a="x y"; set -- ' + "$a" * (n // 2), 2),
            "$a$a in a for list": ('a="x y"; for i in ' + "$a" * (n // 2) + "; do :; done", 2),
            "modifier repeated": ("$a:sx" * (n // 5), 2),
            "modifier lookalikes": ("$a:" * (n // 3), 0),
            "two-letter $( alphabet": ("$(" * (n // 2), None),
            "unclosed ${": ("${a" * (n // 3), 0),
            "quoted items": ("for x in " + '"a b" ' * (n // 6) + "; do set -- $x; done", 2),
            "heredoc without end": ("cat <<EOF\n" + "$a\n" * (n // 3), 0),
            "escapes": ('a="x y"; set -- ' + "\\$a" * (n // 3), 0),
        }
        for label, (cmd, code) in cases.items():
            with self.subTest(case=label):
                t0 = time.monotonic()
                r = run_hook(cmd)
                elapsed = time.monotonic() - t0
                self.assertLess(elapsed, 2.0, label)
                if code is not None:
                    self.assertEqual(r.returncode, code, (label, r.stderr[:200], r.stdout[:200]))
                else:  # recursion past the limit → ask; anything else must still be an answer
                    self.assertEqual(r.returncode, 0, label)

    # ------------------------------------------------------------ R2-7 / R2-8 (v7.3 r2)

    def test_a_prefix_assignment_does_not_outlive_its_command(self):
        """`NAME=v cmd` sets NAME in cmd's environment only: a later `$NAME` is not this command's value."""
        for cmd in ('MSG="a b" git commit -q; ls $MSG',
                    'FLAGS="--a --b" make; ./deploy.sh $FLAGS',
                    'X="a b" Y=1 env | grep X; set -- $X'):
            with self.subTest(cmd=cmd):
                self.assert_silent(cmd)
                self.assertEqual(G.check(cmd), [])

    def test_a_substitution_in_an_assignment_sees_the_assignments_before_it(self):
        """`x="a b" y=$(printf %s $x)`: zsh assigns left to right, so the substitution sees the multi-word x."""
        for cmd in ('x="a b"; y=$(printf %s $x)',
                    'x="a b" y=$(printf %s $x)',
                    'x="a b" y="$(printf %s $x)" z=1'):
            with self.subTest(cmd=cmd):
                self.assert_blocked(cmd)
        # the order still matters: a substitution BEFORE the assignment sees the old (unset) value
        self.assert_silent('y=$(printf %s $x) x="a b"')

    def test_nesting_past_the_parser_depth_asks(self):
        """R2-8: nesting deeper than cmdparse.MAX_DEPTH is a command the shell WOULD run — ask, like the other
        guards (before r2: a ValueError read as a lexing problem → silent pass)."""
        depth = G.cmdparse.MAX_DEPTH + 2
        cmd = 'a="x y"; echo ' + "$(echo " * depth + "$a" + ")" * depth
        self.assert_ask(run_hook(cmd), "NestingError", "nesting")

    @unittest.skipUnless(WIRED, "hooks.json entry not added yet (owned by slice S1; the integrator adds it)")
    def test_wired(self):
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/hooks/guard-zsh-split.py"', WIRED)


class CheckTest(unittest.TestCase):
    """In-process: the decision function and the shell detection."""

    def test_corpus(self):
        wrong = [(c, b) for c, b in CORPUS if bool(G.check(c)) != b]
        self.assertEqual(wrong, [])

    def test_corpus_size(self):
        self.assertGreaterEqual(len([c for c, b in CORPUS if not b]), 40)

    def test_explicit_split_arrays_arithmetic_not_flagged(self):
        for cmd in (
            'a="x y"; set -- ${=a}',
            'a="x y"; set -- $=a',
            'a=(x y); set -- $a',
            'a=(x y); for i in "${a[@]}"; do :; done',
            'a="x y"; echo $(( ${#a} + 1 ))',
            'a="x y"; set -- $a[1]',
            'a="x y"; set -- "$a"',
            "a=\"x y\"; set -- '$a'",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(G.check(cmd), [])

    def test_hits_name_where(self):
        self.assertEqual(G.check('a="x y"; set -- $a'), [("a", "multi", "`set`")])
        self.assertEqual(G.check('P="a b"; $P x'), [("P", "multi", "command position")])
        self.assertEqual(G.check("f=$(ls); for x in $f; do :; done"), [("f", "subst", "a `for … in` list")])
        self.assertEqual(G.check('export F="a b"; ls $F'), [("F", "multi", "an argument")])
        self.assertEqual(G.check("git show $U:src/x"), [("U", "modifier", "s")])

    def test_internal_error_asks_in_process(self):
        with mock.patch.object(G.cmdparse, "lex", side_effect=RuntimeError("boom")), mock.patch.dict(
            os.environ, {"SHELL": FAKE_ZSH}
        ), mock.patch.object(sys, "stdin", io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "set -- $a"}}))), mock.patch.object(
            sys, "stdout", io.StringIO()
        ) as out:
            os.environ.pop("CLAUDE_CODE_SHELL", None)
            os.environ.pop("CMK_ZSH_GUARD", None)
            self.assertEqual(G.main(), 0)
        decision = json.loads(out.getvalue())["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "ask")
        self.assertIn("RuntimeError: boom", decision["permissionDecisionReason"])

    def test_shell_detection_order(self):
        empty = os.path.join(TMP, "empty")
        os.makedirs(empty, exist_ok=True)
        only_bash = os.path.join(TMP, "only-bash")
        os.makedirs(only_bash, exist_ok=True)
        if not os.path.exists(os.path.join(only_bash, "bash")):
            os.symlink(FAKE_BASH, os.path.join(only_bash, "bash"))
        not_exec = os.path.join(TMP, "noexec", "zsh")
        os.makedirs(os.path.dirname(not_exec), exist_ok=True)
        open(not_exec, "w").close()
        with mock.patch.object(G, "STANDARD_DIRS", ()):
            d = G.bash_tool_shell
            self.assertEqual(d({"CLAUDE_CODE_SHELL": FAKE_BASH, "SHELL": FAKE_ZSH, "PATH": empty}), "bash")
            self.assertEqual(d({"CLAUDE_CODE_SHELL": "/no/such/zsh", "SHELL": FAKE_BASH, "PATH": empty}), "bash")
            self.assertEqual(d({"SHELL": FAKE_ZSH, "PATH": empty}), "zsh")
            self.assertEqual(d({"SHELL": not_exec, "PATH": empty}), None)
            self.assertEqual(d({"SHELL": "/usr/bin/fish", "PATH": SHELLS}), "zsh")  # zsh first, then bash
            self.assertEqual(d({"SHELL": "/usr/bin/fish", "PATH": only_bash}), "bash")
            self.assertEqual(d({"SHELL": "/usr/bin/fish", "PATH": empty}), None)
        with mock.patch.object(G, "STANDARD_DIRS", (SHELLS,)):
            self.assertEqual(G.bash_tool_shell({"SHELL": "/usr/bin/fish", "PATH": empty}), "zsh")


class CmdparseLexTest(unittest.TestCase):
    """The 7.3 lexer additions the guard relies on (quoting mask, array flag, arith items)."""

    def words(self, command):
        return [w for kind, val in G.cmdparse.lex(command) if kind == "cmd" for w in val]

    def test_quoting_mask(self):
        w = self.words("x\"a $b\"'c'\\$d$e")[0]
        self.assertEqual(str(w), "xa $bc$d$e")
        self.assertEqual(w.quoting, "u" + "dddd" + "s" + "s" + "u" + "uu")  # x · "a $b" · 'c' · \$ · d · $e

    def test_mask_length_matches_word(self):
        for cmd in ('a "b\\"c" $(x) `y` $\'z\\n\' "$(q)r" 2>err', "echo \\\n x", '""'):
            for kind, val in G.cmdparse.lex(cmd):
                if kind in ("cmd", "redir"):
                    for w in val:
                        with self.subTest(cmd=cmd, word=str(w)):
                            self.assertEqual(len(w.quoting), len(w))

    def test_array_flag(self):
        self.assertTrue(self.words("a=(x y)")[0].array)
        self.assertFalse(self.words('a="x y"')[0].array)
        self.assertFalse(self.words("'a='(x)")[0].array)

    def test_arith_item(self):
        kinds = [k for k, _ in G.cmdparse.lex("echo $((1 + 2)) $(date)")]
        self.assertEqual(kinds, ["arith", "sub", "cmd"])

    def test_walk_still_sees_commands_inside_arith(self):
        calls = G.cmdparse.git_calls("echo $(( $(git reset --hard) ))", "/tmp")
        self.assertEqual([c["sub"] for c in calls], ["reset"])


if __name__ == "__main__":
    unittest.main()
