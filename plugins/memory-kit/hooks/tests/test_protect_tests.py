#!/usr/bin/env python3
"""Tests for hooks/protect-tests.py (v2) — run: python3 plugins/memory-kit/hooks/tests/test_protect_tests.py

Every case feeds hook JSON through the EXACT command string registered in hooks.json, with
CLAUDE_PLUGIN_ROOT and CLAUDE_PROJECT_DIR exported and `python3` pinned to the interpreter running
the tests. CMK_ALLOW_TEST_EDITS is removed from the environment unless a case sets it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
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


WIRING = wiring("Edit|Write", "protect-tests.py")

JS_TEST = """import { sum } from '../src/sum';

describe('sum', () => {
  it('adds', () => {
    const x = 2;
    expect(sum(x, 3)).toBe(5);
  });
});
"""


class ProtectTestsV2(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="cmk-pt-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        os.makedirs(os.path.join(self.root, "tests"))
        self.test_file = os.path.join(self.root, "tests", "sum.test.ts")
        with open(self.test_file, "w") as fh:
            fh.write(JS_TEST)
        self.env = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT, CLAUDE_PROJECT_DIR=self.root,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        self.env.pop("CMK_ALLOW_TEST_EDITS", None)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.shim, ignore_errors=True)

    def run_hook(self, tool, tool_input, env=None, session="s1"):
        payload = json.dumps({"session_id": session, "tool_name": tool, "tool_input": tool_input})
        r = subprocess.run(WIRING, shell=True, input=payload, capture_output=True, text=True, env=env or self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return "silent", ""
        out = json.loads(r.stdout)["hookSpecificOutput"]
        return out["permissionDecision"], out["permissionDecisionReason"]

    def edit(self, old, new, **kw):
        return self.run_hook("Edit", {"file_path": self.test_file, "old_string": old, "new_string": new}, **kw)

    # --- the spec's cases -------------------------------------------------------------
    def test_changed_expectation_asks(self):
        decision, reason = self.edit("    expect(sum(x, 3)).toBe(5);", "    expect(sum(x, 3)).toBe(6);")
        self.assertEqual(decision, "ask")
        self.assertIn("toBe(5)", reason)

    def test_pure_addition_is_silent(self):
        old = "    expect(sum(x, 3)).toBe(5);\n"
        new = old + "    expect(sum(x, 0)).toBe(2);\n"
        self.assertEqual(self.edit(old, new), ("silent", ""))

    def test_it_to_it_skip_asks(self):
        decision, reason = self.edit("  it('adds', () => {", "  it.skip('adds', () => {")
        self.assertEqual(decision, "ask")
        self.assertIn("skip/only", reason)

    def test_rename_outside_assertions_is_silent(self):
        self.assertEqual(self.edit("    const x = 2;", "    const two = 2;"), ("silent", ""))

    def test_allow_env_is_silent(self):
        env = dict(self.env, CMK_ALLOW_TEST_EDITS="1")
        self.assertEqual(self.edit("    expect(sum(x, 3)).toBe(5);", "", env=env), ("silent", ""))
        self.assertEqual(self.run_hook("Write", {"file_path": self.test_file + ".snap", "content": "x"}, env=env),
                         ("silent", ""))

    # --- the rest of the contract -----------------------------------------------------
    def test_deleted_assertion_asks(self):
        self.assertEqual(self.edit("    expect(sum(x, 3)).toBe(5);\n", "")[0], "ask")

    def test_python_assert_and_pytest_tokens(self):
        py = os.path.join(self.root, "tests", "test_calc.py")
        with open(py, "w") as fh:
            fh.write("def test_calc():\n    assert calc(2) == 4\n")

        def edit_py(old, new):
            return self.run_hook("Edit", {"file_path": py, "old_string": old, "new_string": new})

        self.assertEqual(edit_py("    assert calc(2) == 4", "    assert calc(2) == 5")[0], "ask")
        self.assertEqual(edit_py("def test_calc():", "@pytest.mark.skip\ndef test_calc():")[0], "ask")
        self.assertEqual(edit_py("def test_calc():", "def test_calc_doubles():"), ("silent", ""))

    def test_only_and_todo_ask(self):
        self.assertEqual(self.edit("describe('sum', () => {", "describe.only('sum', () => {")[0], "ask")
        self.assertEqual(self.edit("});\n", "});\ntest.todo('negative numbers');\n")[0], "ask")

    def test_exit_is_not_xit(self):
        self.assertEqual(self.edit("    const x = 2;", "    const x = 2; process.exit;"), ("silent", ""))

    def test_reindent_only_is_silent(self):
        self.assertEqual(self.edit("    expect(sum(x, 3)).toBe(5);", "      expect(sum(x, 3)).toBe(5);"),
                         ("silent", ""))

    def test_write_uses_disk_content(self):
        weaker = JS_TEST.replace("toBe(5)", "toBe(6)")
        self.assertEqual(self.run_hook("Write", {"file_path": self.test_file, "content": weaker})[0], "ask")
        stronger = JS_TEST.replace("  });\n});", "    expect(sum(1, 1)).toBe(2);\n  });\n});")
        self.assertEqual(self.run_hook("Write", {"file_path": self.test_file, "content": stronger}),
                         ("silent", ""))

    def test_snap_asks(self):
        snap = os.path.join(self.root, "tests", "__snapshots__", "sum.test.ts.snap")
        self.assertEqual(self.run_hook("Write", {"file_path": snap, "content": "exports[`a`] = `1`;"})[0], "ask")
        self.assertEqual(self.run_hook("Edit", {"file_path": snap, "old_string": "1", "new_string": "2"})[0], "ask")

    def test_new_and_session_created_files_stay_silent(self):
        new_file = os.path.join(self.root, "tests", "new.test.ts")
        self.assertEqual(self.run_hook("Write", {"file_path": new_file, "content": "expect(1).toBe(1);"}),
                         ("silent", ""))
        with open(new_file, "w") as fh:
            fh.write("expect(1).toBe(1);\n")
        # the red→green loop on the session's own file: even a changed expectation is silent
        self.assertEqual(self.run_hook("Edit", {"file_path": new_file, "old_string": "expect(1).toBe(1);",
                                                "new_string": "expect(1).toBe(2);"}), ("silent", ""))
        # another session editing it is back under the rule
        self.assertEqual(self.run_hook("Edit", {"file_path": new_file, "old_string": "expect(1).toBe(1);",
                                                "new_string": "expect(1).toBe(2);"}, session="s2")[0], "ask")

    def test_non_test_and_exempt_files_are_silent(self):
        src = os.path.join(self.root, "src", "sum.ts")
        self.assertEqual(self.run_hook("Edit", {"file_path": src, "old_string": "expect(", "new_string": ""}),
                         ("silent", ""))
        fixture = os.path.join(self.root, "tests", "data.json")
        with open(fixture, "w") as fh:
            fh.write("{}")
        self.assertEqual(self.run_hook("Write", {"file_path": fixture, "content": "[]"}), ("silent", ""))

    def test_garbage_is_silent(self):
        r = subprocess.run(WIRING, shell=True, input="not json", capture_output=True, text=True, env=self.env)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main(verbosity=1)
