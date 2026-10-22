#!/usr/bin/env python3
"""Session start flags a project that wires its own copy of a kit hook (AC-7, v7.3) — run:
python3 plugins/memory-kit/hooks/tests/test_legacy_hooks.py

Repos adopted before the plugin existed copied the kit's hooks into `.claude/hooks/` and wired them in
`.claude/settings.json`; with the plugin installed both fire (two PreCompact blocks, two SessionStart injections).
The detector (`hooks/lib/legacy_hooks.py`) reads the project's settings files, resolves each wired script and
flags it on a POSITIVE signal in its CONTENT, by event — never on its file name:
  PreCompact    emits `"decision": "block"` and names MEMORY.md
  SessionStart  reads `.claude/memory/MEMORY.md` and prints `additionalContext`
  SessionEnd    logs the kit's `[hook] SessionEnd: session=` line
  PreToolUse    a test-file guard (`Protect test files from modification`, `Test files are protected`,
                `CMK_ALLOW_TEST_EDITS`)
Skipped when the project's settings disable the plugin. Shown on startup and clear only.

Every case runs the EXACT SessionStart commands from hooks.json (all six parts) against a throwaway repo and
reads the injected text. What this proves: which wiring the nudge names on these fixtures. Its false-positive
count over the real adopter repos is a separate measurement (reported with the release).
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
with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as _fh:
    PARTS = [h["command"] for h in json.load(_fh)["hooks"]["SessionStart"][0]["hooks"]]
NUDGE = "copies of the kit's hooks"
CAP = 10_000

KIT_PRECOMPACT = """#!/bin/bash
MEMORY_FILE="$PROJECT_DIR/.claude/memory/MEMORY.md"
cat << HOOKJSON
{"decision": "block", "reason": "CONTEXT COMPRESSION IMMINENT — save MEMORY.md"}
HOOKJSON
"""
KIT_SESSION_START = '''import json
from pathlib import Path
MEMORY_FILE = PROJECT_DIR / ".claude" / "memory" / "MEMORY.md"
content = MEMORY_FILE.read_text(encoding="utf-8")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": content}}))
'''
SLIM_SESSION_START = '''"""Project-only context: STATUS.md and nudges. MEMORY.md travels with the plugin."""
import json
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": open("docs/STATUS.md").read()}}))
'''
KIT_SESSION_END = """#!/usr/bin/env bash
LOG_FILE="$STATE_DIR/session-end.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') [hook] SessionEnd: session=$SESSION_ID" >> "$LOG_FILE"
"""
KIT_PROTECT_TESTS = """#!/bin/bash
# Hook: Protect test files from modification
echo "BLOCKED: Test files are protected. Fix the implementation, not the tests." >&2
exit 2
"""
UNRELATED = """#!/bin/bash
# a project's own hook: prints the daily plan
cat docs/plan.md
"""


def wired(event, script, runner="bash"):
    return {event: [{"hooks": [{"type": "command", "command": '%s "$CLAUDE_PROJECT_DIR/.claude/hooks/%s"' % (runner, script)}]}]}


class LegacyHooks(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="cmk-legacy-repo-")
        self.home = tempfile.mkdtemp(prefix="cmk-legacy-home-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=self.repo, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        for var in ("CMK_INJECT_BUDGET", "CMK_ALLOW_TEST_EDITS"):
            self.env.pop(var, None)
        self.write(".claude/memory/MEMORY.md", "# Hot\n\n- [2026-01-01] CANARY\n")

    def tearDown(self):
        for d in (self.repo, self.home, self.shim):
            shutil.rmtree(d, ignore_errors=True)

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def settings(self, hooks, rel=".claude/settings.json", **extra):
        self.write(rel, json.dumps(dict(extra, hooks=hooks)))

    def injected(self, source="startup"):
        procs = [subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, env=self.env) for cmd in PARTS]
        text = ""
        for p in procs:
            out, err = p.communicate(json.dumps({"session_id": "s", "source": source}))
            self.assertEqual(p.returncode, 0, err)
            if out.strip():
                ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
                self.assertLessEqual(len(ctx.encode("utf-16-le")) // 2, CAP)
                text += ctx
        return text

    def test_each_kit_copy_is_flagged_by_content(self):
        cases = [
            ("PreCompact", "pre-compact.sh", KIT_PRECOMPACT, "bash"),
            ("SessionStart", "session-start.py", KIT_SESSION_START, "python3"),
            ("SessionEnd", "session-end.sh", KIT_SESSION_END, "bash"),
            ("PreToolUse", "protect-tests.sh", KIT_PROTECT_TESTS, "bash"),
        ]
        for event, script, body, runner in cases:
            with self.subTest(event=event):
                self.write(".claude/hooks/" + script, body)
                self.settings(wired(event, script, runner))
                text = self.injected()
                self.assertIn(NUDGE, text)
                self.assertIn(".claude/hooks/%s" % script, text)
                self.assertIn(event, text)

    def test_a_renamed_copy_is_still_flagged(self):
        self.write(".claude/hooks/save-before-compact.sh", KIT_PRECOMPACT)
        self.settings(wired("PreCompact", "save-before-compact.sh"))
        self.assertIn(".claude/hooks/save-before-compact.sh", self.injected())

    def test_a_kit_named_file_with_project_content_is_not_flagged(self):
        """Never the file name: a slimmed project session-start (no MEMORY.md) and an unrelated pre-compact.sh."""
        self.write(".claude/hooks/session-start.py", SLIM_SESSION_START)
        self.write(".claude/hooks/pre-compact.sh", UNRELATED)
        hooks = wired("SessionStart", "session-start.py", "python3")
        hooks.update(wired("PreCompact", "pre-compact.sh"))
        self.settings(hooks)
        self.assertNotIn(NUDGE, self.injected())

    def test_a_copy_under_another_event_is_not_flagged(self):
        """periodic-save.sh (a Stop hook of old kits) also emits a block: the event must match the kit hook."""
        self.write(".claude/hooks/periodic-save.sh", KIT_PRECOMPACT)
        self.settings(wired("Stop", "periodic-save.sh"))
        self.assertNotIn(NUDGE, self.injected())

    def test_plugin_disabled_in_the_project_is_skipped(self):
        self.write(".claude/hooks/pre-compact.sh", KIT_PRECOMPACT)
        self.settings(wired("PreCompact", "pre-compact.sh"), enabledPlugins={"memory-kit@memory-kit": False})
        self.assertNotIn(NUDGE, self.injected())
        # a local override that enables it again brings the nudge back
        self.write(".claude/settings.local.json", json.dumps({"enabledPlugins": {"memory-kit@memory-kit": True}}))
        self.assertIn(NUDGE, self.injected())

    def test_local_settings_are_read_too(self):
        self.write(".claude/hooks/session-end.sh", KIT_SESSION_END)
        self.settings(wired("SessionEnd", "session-end.sh"), rel=".claude/settings.local.json")
        self.assertIn("settings.local.json", self.injected())

    def test_startup_and_clear_only(self):
        self.write(".claude/hooks/pre-compact.sh", KIT_PRECOMPACT)
        self.settings(wired("PreCompact", "pre-compact.sh"))
        for source, shown in (("startup", True), ("clear", True), ("resume", False), ("compact", False),
                              ("fork", False)):
            with self.subTest(source=source):
                self.assertEqual(NUDGE in self.injected(source), shown)

    def test_broken_settings_and_missing_scripts_are_quiet(self):
        self.write(".claude/settings.json", "{not json")
        self.assertNotIn(NUDGE, self.injected())
        self.settings(wired("PreCompact", "missing.sh"))
        self.assertNotIn(NUDGE, self.injected())
        self.settings({"PreCompact": "not a list", "SessionEnd": [{"hooks": "x"}, "y"]})
        self.assertNotIn(NUDGE, self.injected())


if __name__ == "__main__":
    unittest.main(verbosity=1)
