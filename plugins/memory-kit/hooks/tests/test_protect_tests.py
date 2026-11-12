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

    def test_missing_state_lib_degrades_the_ledger_never_the_guard(self):
        """R2-6: a plugin copy without hooks/lib/statefs.py (a partial install, an old cache) — the session ledger is
        best-effort, the guard still answers: a new test file is silent, a weakening edit of an existing one asks, a
        pure addition is silent, and nothing crashes (before r2: ModuleNotFoundError, exit 1)."""
        broken = tempfile.mkdtemp(prefix="cmk-pt-nolib-")
        self.addCleanup(shutil.rmtree, broken, True)
        shutil.copytree(os.path.join(PLUGIN_ROOT, "hooks"), os.path.join(broken, "hooks"))
        os.remove(os.path.join(broken, "hooks", "lib", "statefs.py"))
        env = dict(self.env, CLAUDE_PLUGIN_ROOT=broken)
        new_file = os.path.join(self.root, "tests", "fresh.test.ts")
        self.assertEqual(self.run_hook("Write", {"file_path": new_file, "content": "expect(1).toBe(1);"}, env=env),
                         ("silent", ""))
        self.assertEqual(self.edit("    expect(sum(x, 3)).toBe(5);", "    expect(sum(x, 3)).toBe(6);", env=env)[0],
                         "ask")
        old = "    expect(sum(x, 3)).toBe(5);\n"
        self.assertEqual(self.edit(old, old + "    expect(sum(x, 0)).toBe(2);\n", env=env), ("silent", ""))


class ProtectTestsBranchAuthored(unittest.TestCase):
    """8.3.1: a test file the base branch does not have was written on this branch (by any session) — its edits pass;
    a test file the base branch has keeps the full guard; no resolvable base keeps the old behaviour."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cmk-pt-git-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        self.base = os.path.join(self.tmp, "base")
        self.repo = os.path.join(self.tmp, "work")
        g = lambda cwd, *a: subprocess.run(["git", "-C", cwd, *a], check=True, capture_output=True)
        os.makedirs(os.path.join(self.base, "tests"))
        g(self.base, "init", "-q", "-b", "main")
        g(self.base, "config", "user.email", "t@example.com")
        g(self.base, "config", "user.name", "t")
        with open(os.path.join(self.base, "tests", "theirs.test.ts"), "w") as fh:
            fh.write(JS_TEST)
        g(self.base, "add", ".")
        g(self.base, "commit", "-q", "-m", "base")
        subprocess.run(["git", "clone", "-q", "-o", "upstream", self.base, self.repo], check=True, capture_output=True)
        g(self.repo, "config", "user.email", "t@example.com")
        g(self.repo, "config", "user.name", "t")
        g(self.repo, "checkout", "-q", "-b", "feature")
        self.ours = os.path.join(self.repo, "tests", "ours.test.ts")
        with open(self.ours, "w") as fh:
            fh.write(JS_TEST)
        g(self.repo, "add", ".")
        g(self.repo, "commit", "-q", "-m", "ours")
        self.theirs = os.path.join(self.repo, "tests", "theirs.test.ts")
        self.env = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT, CLAUDE_PROJECT_DIR=self.repo,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        self.env.pop("CMK_ALLOW_TEST_EDITS", None)
        self.env.pop("CMK_TEST_BASE_REF", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.shim, ignore_errors=True)

    def edit(self, path, env=None):
        payload = json.dumps({"session_id": "s9", "tool_name": "Edit", "tool_input": {
            "file_path": path, "old_string": "    expect(sum(x, 3)).toBe(5);", "new_string": "    expect(sum(x, 3)).toBe(6);"}})
        r = subprocess.run(WIRING, shell=True, input=payload, capture_output=True, text=True, env=env or self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else "silent"

    def test_branch_authored_test_passes(self):
        self.assertEqual(self.edit(self.ours), "silent")

    def test_test_on_the_base_branch_still_asks(self):
        self.assertEqual(self.edit(self.theirs), "ask")

    def test_no_resolvable_base_keeps_the_guard(self):
        subprocess.run(["git", "-C", self.repo, "remote", "remove", "upstream"], check=True, capture_output=True)
        self.assertEqual(self.edit(self.ours), "ask")

    def test_pinned_base_wins(self):
        # pinned to the feature branch itself: the file exists there, so the guard applies
        self.assertEqual(self.edit(self.ours, env=dict(self.env, CMK_TEST_BASE_REF="feature")), "ask")

    def orphan(self):
        """An unrelated commit (empty tree, no parent) made without touching the work tree."""
        run = lambda *a: subprocess.run(["git", "-C", self.repo, *a], check=True, capture_output=True, text=True,
                                       input="").stdout.strip()
        empty = run("hash-object", "-t", "tree", "-w", "--stdin")
        return run("commit-tree", empty, "-m", "orphan")

    def test_local_branch_named_like_the_base_cannot_stand_in(self):
        g = lambda *a: subprocess.run(["git", "-C", self.repo, *a], check=True, capture_output=True)
        g("remote", "remove", "upstream")
        g("update-ref", "refs/heads/upstream/main", self.orphan())
        self.assertEqual(self.edit(self.ours), "ask")

    def test_unrelated_remote_ref_keeps_the_guard(self):
        g = lambda *a: subprocess.run(["git", "-C", self.repo, *a], check=True, capture_output=True)
        g("update-ref", "refs/remotes/upstream/main", self.orphan())
        subprocess.run(["git", "-C", self.repo, "update-ref", "-d", "refs/remotes/upstream/HEAD"], capture_output=True)
        self.assertEqual(self.edit(self.ours), "ask")

    def test_unresolvable_pin_falls_back_to_candidates(self):
        self.assertEqual(self.edit(self.ours, env=dict(self.env, CMK_TEST_BASE_REF="nope/none")), "silent")


if __name__ == "__main__":
    unittest.main(verbosity=1)
