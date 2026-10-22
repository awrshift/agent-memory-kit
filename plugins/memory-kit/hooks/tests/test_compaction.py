#!/usr/bin/env python3
"""PreCompact by trigger, and the nudge after an auto compaction over unsaved memory (AC-1, AC-2, v7.3) — run:
python3 plugins/memory-kit/hooks/tests/test_compaction.py

Platform fact (code.claude.com/docs/en/hooks §PreCompact, read 2026-10-22): blocking an AUTO compaction either
skips it (proactive) or FAILS the current request (recovery from a context-limit error). So pre-compact.sh blocks
only a `manual` /compact; on `auto` (or no trigger) it lets compaction run and leaves `.claude/state/compact-unsaved`;
the SessionStart run for source `compact` that follows puts a loud "save MEMORY.md now" line at the head of the
memory section and the writing part (part 1) clears the marker.

Every case runs the EXACT command strings from hooks.json through a shell (python3 pinned to this interpreter).
What this proves: what each hook prints and leaves on disk. What it cannot see: that Claude Code runs SessionStart
`compact` right after the compaction (the platform doc says it does).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as _fh:
    _CFG = json.load(_fh)["hooks"]
PRECOMPACT = _CFG["PreCompact"][0]["hooks"][0]["command"]
PARTS = [h["command"] for h in _CFG["SessionStart"][0]["hooks"]]
NUDGE = "COMPACTION RAN OVER UNSAVED MEMORY"
CAP = 10_000


def units(text):
    return len(text.encode("utf-16-le")) // 2


class Compaction(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="cmk-compact-repo-")
        self.home = tempfile.mkdtemp(prefix="cmk-compact-home-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=self.repo, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        for var in ("CMK_INJECT_BUDGET", "CMK_ALLOW_TEST_EDITS"):
            self.env.pop(var, None)
        self.marker = os.path.join(self.repo, ".claude", "state", "compact-unsaved")

    def tearDown(self):
        for d in (self.repo, self.home, self.shim):
            shutil.rmtree(d, ignore_errors=True)

    def write(self, rel, text, age_seconds=0):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        if age_seconds:
            t = time.time() - age_seconds
            os.utime(path, (t, t))
        return path

    def memory(self, age_seconds, lines=10):
        body = "# Hot cache\n\n**Current state:** CANARY-STATE.\n\n" + "".join(
            "- [2026-01-01] durable pattern %d\n" % k for k in range(lines))
        self.write(".claude/memory/MEMORY.md", body, age_seconds)

    def precompact(self, payload):
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        r = subprocess.run(PRECOMPACT, shell=True, input=raw, capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def parts(self, source, which=range(1, 7), session="sess-1"):
        procs = {n: subprocess.Popen(PARTS[n - 1], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, env=self.env) for n in which}
        out = {}
        for n, p in procs.items():
            stdout, stderr = p.communicate(json.dumps({"session_id": session, "source": source}))
            self.assertEqual(p.returncode, 0, stderr)
            out[n] = json.loads(stdout)["hookSpecificOutput"]["additionalContext"] if stdout.strip() else None
        return out

    # ------------------------------------------------------------------ AC-1: PreCompact by trigger

    def test_auto_over_stale_memory_never_blocks_and_leaves_the_marker(self):
        self.memory(age_seconds=3600)
        for payload in ({"session_id": "s", "trigger": "auto"}, {"session_id": "s"}, ""):
            with self.subTest(payload=payload):
                if os.path.exists(self.marker):
                    os.remove(self.marker)
                out = self.precompact(payload)
                self.assertNotIn("decision", out)
                with open(self.marker, encoding="utf-8") as fh:
                    lines = fh.read().splitlines()
                self.assertEqual(len(lines), 1)
                self.assertRegex(lines[0], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\t.*stale")

    def test_auto_over_a_cap_never_blocks_and_names_the_cap(self):
        self.memory(age_seconds=0, lines=200)
        out = self.precompact({"trigger": "auto"})
        self.assertNotIn("decision", out)
        with open(self.marker, encoding="utf-8") as fh:
            self.assertIn("OVER its caps", fh.read())

    def test_manual_over_stale_memory_still_blocks(self):
        self.memory(age_seconds=3600)
        out = self.precompact({"session_id": "s", "trigger": "manual", "custom_instructions": None})
        self.assertEqual(out.get("decision"), "block")
        self.assertIn("stale", out["reason"])
        self.assertFalse(os.path.exists(self.marker))

    def test_manual_over_a_cap_still_blocks(self):
        self.memory(age_seconds=0, lines=200)
        out = self.precompact({"trigger": "manual"})
        self.assertEqual(out.get("decision"), "block")
        self.assertIn("OVER its caps", out["reason"])

    def test_fresh_memory_allows_both_and_clears_an_old_marker(self):
        self.memory(age_seconds=0)
        self.write(".claude/state/compact-unsaved", "2026-01-01 00:00:00\tan old reason\n")
        for trigger in ("auto", "manual"):
            with self.subTest(trigger=trigger):
                self.assertEqual(self.precompact({"trigger": trigger}), {})
                self.assertFalse(os.path.exists(self.marker))

    def test_unadopted_repo_writes_nothing(self):
        self.assertEqual(self.precompact({"trigger": "auto"}), {})
        self.assertEqual(os.listdir(self.repo), [])

    # ------------------------------------------------------------------ AC-2: the nudge after compaction

    def test_auto_compaction_then_session_start_nudges_once_and_clears(self):
        self.memory(age_seconds=3600)
        self.write("context/handoffs/h-2026-01-01.md", "# Handoff\n\nnext: X\n")
        self.precompact({"session_id": "sess-1", "trigger": "auto"})
        self.assertTrue(os.path.exists(self.marker))
        printed = self.parts("compact")
        present = [ctx for ctx in printed.values() if ctx]
        for ctx in present:
            self.assertLessEqual(units(ctx), CAP)
        joined = "".join(present)
        self.assertEqual(joined.count(NUDGE), 1, joined[:3000])
        self.assertIn("stale", joined[joined.index(NUDGE):joined.index(NUDGE) + 400])
        self.assertIn("save MEMORY.md now", joined)
        # the nudge is in the part that carries the memory section, ahead of the memory body
        carrier = [ctx for ctx in present if "MEMORY.md (hot cache" in ctx][0]
        self.assertLess(carrier.index("MEMORY.md (hot cache"), carrier.index(NUDGE))
        self.assertLess(carrier.index(NUDGE), carrier.index("CANARY-STATE"))
        self.assertFalse(os.path.exists(self.marker))
        # the next compaction of another session does not repeat it
        self.assertNotIn(NUDGE, "".join(c for c in self.parts("compact", session="sess-2").values() if c))

    def test_read_only_parts_see_the_nudge_and_leave_the_marker(self):
        self.memory(age_seconds=3600, lines=400)  # memory over a part: the section spans parts
        self.precompact({"session_id": "sess-1", "trigger": "auto"})
        printed = self.parts("compact", which=range(2, 7))
        self.assertTrue(os.path.exists(self.marker))
        printed.update(self.parts("compact", which=[1]))
        joined = "".join(printed[n] for n in sorted(printed) if printed[n])
        self.assertEqual(joined.count(NUDGE), 1)
        self.assertFalse(os.path.exists(self.marker))

    def test_parts_agree_when_part_one_clears_the_marker_first(self):
        """The race the protocol closes: part 1 has already removed the marker when parts 2..6 run."""
        self.memory(age_seconds=3600, lines=400)
        self.precompact({"session_id": "sess-1", "trigger": "auto"})
        first = self.parts("compact", which=[1])[1]
        self.assertFalse(os.path.exists(self.marker))
        rest = self.parts("compact", which=range(2, 7))
        joined = first + "".join(rest[n] for n in sorted(rest) if rest[n])
        self.assertEqual(joined.count(NUDGE), 1)
        self.assertIn("CANARY-STATE", joined)

    def test_other_sources_neither_nudge_nor_clear(self):
        self.memory(age_seconds=3600)
        self.precompact({"session_id": "sess-1", "trigger": "auto"})
        for src in ("startup", "resume", "clear", "fork"):
            with self.subTest(source=src):
                joined = "".join(c for c in self.parts(src).values() if c)
                self.assertNotIn(NUDGE, joined)
                self.assertTrue(os.path.exists(self.marker))

    def test_no_memory_file_still_nudges(self):
        self.write("context/handoffs/h-2026-01-01.md", "# Handoff\n")
        self.precompact({"session_id": "sess-1", "trigger": "auto"})
        self.assertTrue(os.path.exists(self.marker))
        joined = "".join(c for c in self.parts("compact").values() if c)
        self.assertEqual(joined.count(NUDGE), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
