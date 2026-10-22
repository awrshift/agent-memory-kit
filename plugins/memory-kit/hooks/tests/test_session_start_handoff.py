#!/usr/bin/env python3
"""A handoff over the injection cap still delivers its opening section whole (AC-6, v7.3) — run:
python3 plugins/memory-kit/hooks/tests/test_session_start_handoff.py

session-start.py injects the newest handoff truncated to HANDOFF_INJECT_CAP. The section the next session must
act on — `## 5. [Opening note for next session]` in the kit template, `## 6. [Opening contract]` in a real
adopter's — is written LAST, so a plain cut drops exactly it. Over the cap, a heading matching /opening/i is now
injected first, whole and labelled; the rest follows, truncated to what is left of the cap.

The fixture `fixtures/handoff-opening-last-6k.md` has the shape of a real handoff (6,272 bytes, sections of the
same sizes, the opening section last); its text is synthetic. Every case runs the EXACT SessionStart command from
hooks.json, all six parts at once, and reads what they print. What this proves: the injected TEXT. What it cannot
see: whether the model acts on it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "handoff-opening-last-6k.md")
with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as _fh:
    PARTS = [h["command"] for h in json.load(_fh)["hooks"]["SessionStart"][0]["hooks"]]
HEADER_RE = re.compile(r"^Memory Kit context — part \d+ of \d+ \([^)]*\)\.\n")
CAP = 10_000
HANDOFF_CAP = 6_000


def section(text, heading_re):
    """The section from the first heading matching heading_re to the next heading of the same or higher level."""
    m = re.search(heading_re, text, re.MULTILINE | re.IGNORECASE)
    level = len(m.group(0)) - len(m.group(0).lstrip("#"))
    nxt = re.compile(r"^#{1,%d}\s" % level, re.MULTILINE).search(text, m.end())
    return text[m.start(): nxt.start() if nxt else len(text)].rstrip()


class HandoffOpening(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="cmk-handoff-repo-")
        self.home = tempfile.mkdtemp(prefix="cmk-handoff-home-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=self.repo, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        for var in ("CMK_INJECT_BUDGET", "CMK_ALLOW_TEST_EDITS"):
            self.env.pop(var, None)
        self.write(".claude/memory/MEMORY.md", "# Hot cache\n\n- [2026-01-01] CANARY\n")

    def tearDown(self):
        for d in (self.repo, self.home, self.shim):
            shutil.rmtree(d, ignore_errors=True)

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def injected(self, source="startup"):
        procs = [subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, env=self.env) for cmd in PARTS]
        bodies = []
        for p in procs:
            out, err = p.communicate(json.dumps({"session_id": "s", "source": source}))
            self.assertEqual(p.returncode, 0, err)
            if out.strip():
                ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
                self.assertLessEqual(len(ctx.encode("utf-16-le")) // 2, CAP)
                bodies.append(HEADER_RE.sub("", ctx, count=1))
        text = "".join(bodies)
        start = text.index("## Latest handoff")
        end = text.find("\n---\n", start)
        return text[start: end if end >= 0 else len(text)]

    def test_real_shaped_handoff_delivers_the_opening_section_whole_and_first(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            handoff = fh.read()
        self.assertGreater(len(handoff), HANDOFF_CAP)
        self.write("context/handoffs/s143-2026-10-22.md", handoff)
        block = self.injected()
        opening = section(handoff, r"^##\s+.*opening.*$")
        self.assertIn("OPENING-END-CANARY", opening)
        self.assertIn(opening, block)
        self.assertLess(block.index(opening), block.index("## 1. What was done"))
        self.assertIn("truncated", block)
        self.assertRegex(block[: block.index(opening)], r"(?i)opening section")
        # the whole handoff block stays near the cap: opening whole + the rest cut to what is left
        self.assertLess(len(block), HANDOFF_CAP + 600)

    def test_kit_template_heading_counts_too(self):
        filler = "".join("- [2026-10-22] a line of what happened in the session, item %d\n" % k for k in range(110))
        handoff = ("# Handoff — t (2026-10-22)\n\n## 1. What was done\n\n" + filler +
                   "\n## 5. [Opening note for next session]\n\nStart with X because Y. TEMPLATE-END-CANARY\n")
        self.assertGreater(len(handoff), HANDOFF_CAP)
        self.write("context/handoffs/t-2026-10-22.md", handoff)
        block = self.injected()
        self.assertIn("## 5. [Opening note for next session]\n\nStart with X because Y. TEMPLATE-END-CANARY", block)

    def test_no_opening_heading_keeps_the_plain_cut(self):
        handoff = "# Handoff\n\n## Done\n\n" + "- a thing that happened in the session, nothing else\n" * 160
        self.write("context/handoffs/plain-2026-10-22.md", handoff)
        block = self.injected()
        self.assertIn("…(truncated — read the full file on demand)", block)
        self.assertNotRegex(block, r"(?i)opening section")

    def test_handoff_under_the_cap_is_injected_unchanged(self):
        handoff = "# Handoff\n\n## 1. Done\n\n- x\n\n## 5. [Opening note for next session]\n\nStart with X.\n"
        self.write("context/handoffs/short-2026-10-22.md", handoff)
        block = self.injected()
        self.assertIn(handoff.rstrip(), block)
        self.assertNotIn("truncated", block)


if __name__ == "__main__":
    unittest.main(verbosity=1)
