#!/usr/bin/env python3
"""Tests for scripts/permission-probes.sh — run: python3 plugins/memory-kit/scripts/tests/test_permission_probes.py

A fake `claude` on PATH stands in for the CLI: it DRAINS its stdin (as `claude -p` does when stdin is
not a terminal) and answers with a JSON result whose `permission_denials` depend on the command in the
prompt. Without `</dev/null` on the real call, the first probe would swallow the rest of the file and
only one line would be graded — the regression this suite pins.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "permission-probes.sh")

FAKE_CLAUDE = r"""#!/usr/bin/env python3
import json, sys
sys.stdin.read()
i = sys.argv.index("-p")
prompt = sys.argv[i + 1]
with open(__import__("os").environ["FAKE_LOG"], "a") as fh:
    fh.write(" ".join(sys.argv[i + 2:]) + "\n")
cmd = prompt.split("Command: ", 1)[1]
if "hookblock" in cmd:
    print(json.dumps({"result": "BLOCKED: Memory Kit git guard", "permission_denials": []}))
elif "danger" in cmd or ".env.permtest" in cmd:
    print(json.dumps({"result": "BLOCKED", "permission_denials": [{"tool_name": "Bash"}]}))
else:
    print(json.dumps({"result": "ran " + cmd, "permission_denials": []}))
"""


class PermissionProbes(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="cmk-probes-")
        self.bin = os.path.join(self.dir, "bin")
        self.repo = os.path.join(self.dir, "repo")
        os.makedirs(self.bin)
        os.makedirs(self.repo)
        with open(os.path.join(self.bin, "claude"), "w") as fh:
            fh.write(FAKE_CLAUDE)
        os.chmod(os.path.join(self.bin, "claude"), 0o755)
        self.log = os.path.join(self.dir, "argv.log")
        self.env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"],
                        HARNESS_OUT=os.path.join(self.dir, "out"), FAKE_LOG=self.log)
        self.env.pop("ANTHROPIC_API_KEY", None)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_probes(self, lines, *args):
        probes = os.path.join(self.dir, "probes.txt")
        with open(probes, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        return subprocess.run(["bash", SCRIPT, probes, *args], cwd=self.repo, env=self.env,
                              capture_output=True, text=True)

    def test_every_probe_line_is_graded(self):
        r = self.run_probes(["# comment", "push|git push danger", "", "env|cat .env.permtest",
                             "ctl-status|git status --short", "hook|git hookblock"], "lbl")
        graded = [ln for ln in r.stdout.splitlines() if ln[:3] in ("OK ", "BAD", "REA", "ERR")]
        self.assertEqual(len(graded), 4, r.stdout + r.stderr)
        self.assertTrue(graded[0].startswith("OK  push"))
        self.assertTrue(graded[1].startswith("OK  env"))
        self.assertTrue(graded[2].startswith("OK  ctl-status"))
        self.assertTrue(graded[3].startswith("READ hook"))
        self.assertEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "out", "push-lbl.json")))

    def test_bad_probe_fails_the_run(self):
        r = self.run_probes(["push|git push --dry-run origin x", "ctl-danger|git danger"])
        self.assertIn("BAD push", r.stdout)
        self.assertIn("BAD ctl-danger", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_decoy_created_and_removed_existing_kept(self):
        self.run_probes(["env|cat .env.permtest"])
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".env.permtest")))
        with open(os.path.join(self.repo, ".env.permtest"), "w") as fh:
            fh.write("MINE=1\n")
        self.run_probes(["env|cat .env.permtest"])
        with open(os.path.join(self.repo, ".env.permtest")) as fh:
            self.assertEqual(fh.read(), "MINE=1\n")

    def test_extra_args_reach_claude(self):
        self.run_probes(["ctl-a|echo a"], "x", "--", "--plugin-dir", "/p", "--setting-sources", "project")
        with open(self.log) as fh:
            self.assertIn("--plugin-dir /p --setting-sources project", fh.read())

    def test_variadic_extra_flag_cannot_swallow_the_prompt(self):
        r = self.run_probes(["ctl-a|echo a"], "x", "--", "--allowedTools", "Bash(git push *)")
        self.assertIn("OK  ctl-a", r.stdout)
        with open(self.log) as fh:
            self.assertTrue(fh.read().rstrip().endswith("--allowedTools Bash(git push *)"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
