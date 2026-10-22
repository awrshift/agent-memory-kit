#!/usr/bin/env python3
"""cmdparse: digits before a redirection are an fd only when unquoted and literal (AC-17 third round) — run:
python3 plugins/memory-kit/hooks/tests/test_cmdparse_fd.py

In bash `echo x 2>> f` redirects fd 2, but `echo x '2'>> f` passes "2" as an argument and redirects stdout, and so
does `"$N">> f`. A lexer that reads quoted digits as an fd disagrees with the shell — and every such disagreement
can turn into a wrong verdict of a guard. Also checked: nothing of the digits' word state leaks into the next word.
What this proves: the parser's reading of these command texts. What it cannot see: other shells' grammars.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import cmdparse  # noqa: E402


def parse(command):
    calls = cmdparse.commands(command, "/tmp")
    redirects = [(w.op, str(w)) for c in calls for w in c.get("redirects", ())]
    argv = [[str(w) for w in c["argv"]] for c in calls if c["name"]]
    return redirects, argv


class FdPrefix(unittest.TestCase):
    def test_unquoted_digits_are_the_fd(self):
        self.assertEqual(parse("echo x 2>> f"), ([("2>>", "f")], [["echo", "x"]]))
        self.assertEqual(parse("cat 0< f"), ([("0<", "f")], [["cat"]]))

    def test_quoted_digits_are_an_argument(self):
        for cmd, op, arg in (("echo x '2'>> f", ">>", "2"), ('echo x "2">> f', ">>", "2"),
                             ("echo x \\2>> f", ">>", "2"), ("echo x 1'2'>> f", ">>", "12"), ("cat '0'< f", "<", "0")):
            with self.subTest(cmd=cmd):
                redirects, argv = parse(cmd)
                self.assertEqual(redirects, [(op, "f")])
                self.assertEqual(argv[0][-1], arg)

    def test_dynamic_digits_are_an_argument(self):
        redirects, argv = parse('echo x "$N">> f')
        self.assertEqual(redirects, [(">>", "f")])
        self.assertEqual(argv, [["echo", "x", "$N"]])

    def test_no_word_state_leaks_past_an_fd_prefix(self):
        # the digits' quoting must not reach the redirection target or the next word
        lexed = cmdparse.lex("echo '3'<<EOF x\nbody\nEOF")
        words = [w for kind, val in lexed if kind == "cmd" for w in val]
        self.assertEqual([str(w) for w in words], ["echo", "3", "x"])
        self.assertEqual(words[-1].quoting, "u")
        lexed = cmdparse.lex("echo 3>> f y")
        target = [w for kind, val in lexed if kind == "redir" for w in val][0]
        self.assertEqual((target.op, str(target), target.quoting), ("3>>", "f", "u"))
        words = [w for kind, val in lexed if kind == "cmd" for w in val]
        self.assertEqual([(str(w), w.quoting, w.array) for w in words], [("echo", "uuuu", False), ("y", "u", False)])


if __name__ == "__main__":
    unittest.main(verbosity=1)
