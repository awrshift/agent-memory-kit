#!/usr/bin/env python3
"""Tests for the 7.2 SessionStart parts — run:
python3 plugins/memory-kit/hooks/tests/test_session_start_parts.py

Claude Code caps one hook's additionalContext at 10,000 characters; over it the model gets a file
path and a 2,000-char preview. hooks.json therefore runs session-start.py six times (`--part 1..6`),
in parallel, as Claude Code does. Every case runs those EXACT command strings from hooks.json
through a shell (python3 pinned to the interpreter running the tests) — all six at once — and
compares what they print with the unsplit output of the same script (no `--part` flag).

What this proves: the transport (sizes, lossless split, read-only parts 2..6, the overflow line).
What it cannot see: whether the model reads the parts — that is the model-level probe in the
release gate (docs/CHANGELOG.md 7.2.0).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(PLUGIN_ROOT, "hooks", "session-start.py")
with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as _fh:
    GROUP = json.load(_fh)["hooks"]["SessionStart"][0]
WIRINGS = [h["command"] for h in GROUP["hooks"]]
UNSPLIT = re.sub(r" --part 1$", "", WIRINGS[0])
SOURCES = ("startup", "clear", "fork", "resume", "compact")
CAP = 10_000
HEADER_RE = re.compile(r"^Memory Kit context — part (\d+) of (\d+) \(parts arrive in any order; together they are the whole\)\.\n")
OVERFLOW = ("Memory Kit: context exceeds 6 parts — the rest is NOT loaded; read .claude/memory/MEMORY.md now "
            "and run /memory-kit:memory-audit.")
CUT_MARK = " […line continues in the next part]\n"


def units(text):
    return len(text.encode("utf-16-le")) // 2


def memory_text(target_bytes, long_line=0):
    """A MEMORY.md of about target_bytes: topic sections of ~1.2 KB, dated lines of ~150 chars."""
    out = ["# Hot cache\n", "\n", "**Current state:** fixture CANARY-STATE line.\n", "\n"]
    if long_line:
        out.append("- [2026-01-01] LONG " + "x" * long_line + " END-OF-LONG\n")
    topic = 0
    while sum(len(x) for x in out) < target_bytes:
        topic += 1
        out.append("\n## Topic %d\n\n" % topic)
        for k in range(8):
            out.append("- [2026-01-%02d] topic %d fact %d — %s\n" % (k + 1, topic, k, "lorem ipsum dolor " * 7))
    return "".join(out)


class Parts(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="cmk-parts-repo-")
        self.home = tempfile.mkdtemp(prefix="cmk-parts-home-")
        self.shim = tempfile.mkdtemp(prefix="cmk-py-")
        os.symlink(sys.executable, os.path.join(self.shim, "python3"))
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=self.repo, CLAUDE_PLUGIN_ROOT=PLUGIN_ROOT,
                        PATH=self.shim + os.pathsep + os.environ["PATH"])
        for var in ("CMK_INJECT_BUDGET", "CMK_ALLOW_TEST_EDITS", "CMK_GIT_GUARD", "CMK_SECRETS_GUARD"):
            self.env.pop(var, None)

    def tearDown(self):
        for d in (self.repo, self.home, self.shim):
            shutil.rmtree(d, ignore_errors=True)

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def fixture(self, memory_bytes, long_line=0, index_bytes=1500, handoff_lines=120):
        self.write(".claude/memory/MEMORY.md", memory_text(memory_bytes, long_line))
        self.write("context/handoffs/work-2026-01-01.md",
                   "# Handoff\n\n## Done\n\n" + "- a thing that happened in the session\n" * handoff_lines)
        self.write("knowledge/index.md", "# Knowledge index\n\n" + "- [concept](concepts/x.md) — a line\n"
                   * (index_bytes // 36))

    def payload(self, source):
        return json.dumps({"session_id": "sess-1", "source": source})

    def state_files(self):
        state = os.path.join(self.repo, ".claude", "state")
        saved = {}
        for name in ("session_count", "session_last"):
            path = os.path.join(state, name)
            saved[name] = open(path).read() if os.path.exists(path) else None
        return saved

    def restore_state(self, saved):
        state = os.path.join(self.repo, ".claude", "state")
        for name, text in saved.items():
            path = os.path.join(state, name)
            if text is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                with open(path, "w") as fh:
                    fh.write(text)

    def reference(self, source):
        """The unsplit text, run without leaving a trace (the counter is put back)."""
        saved = self.state_files()
        r = subprocess.run(UNSPLIT, shell=True, input=self.payload(source), capture_output=True, text=True,
                           env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.restore_state(saved)
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]

    def run_parts(self, source, which=range(1, 7)):
        """All requested parts started at once, like Claude Code runs matching hooks: {n: context or None}."""
        procs = {}
        for n in which:
            procs[n] = subprocess.Popen(WIRINGS[n - 1], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, env=self.env)
        out = {}
        for n, p in procs.items():
            stdout, stderr = p.communicate(self.payload(source))
            self.assertEqual(p.returncode, 0, stderr)
            out[n] = json.loads(stdout)["hookSpecificOutput"]["additionalContext"] if stdout.strip() else None
        return out

    def split(self, printed):
        """(K, [bodies in part order]) after checking every wrapper line."""
        present = {n: ctx for n, ctx in printed.items() if ctx is not None}
        self.assertIn(1, present)
        ks = set()
        bodies = []
        for n in sorted(present):
            m = HEADER_RE.match(present[n])
            self.assertIsNotNone(m, present[n][:200])
            self.assertEqual(int(m.group(1)), n)
            ks.add(int(m.group(2)))
            bodies.append(present[n][m.end():])
        self.assertEqual(len(ks), 1, ks)
        k = ks.pop()
        self.assertEqual(sorted(present), list(range(1, min(k, 6) + 1)))
        return k, bodies

    def check_lossless(self, source, allow_cut=False):
        ref = self.reference(source)
        printed = self.run_parts(source)
        for n, ctx in printed.items():
            if ctx is not None:
                self.assertLessEqual(units(ctx), CAP, "part %d: %d UTF-16 units" % (n, units(ctx)))
                self.assertLessEqual(len(ctx), CAP)
        k, bodies = self.split(printed)
        self.assertLessEqual(k, 6)
        joined = "".join(bodies)
        if allow_cut:
            joined = joined.replace(CUT_MARK, "")
        self.assertEqual(joined, ref)
        for body in bodies:  # a part ends at a line end: no line split except an over-long one
            self.assertTrue(body.endswith("\n"))
            if not allow_cut:
                self.assertNotIn(CUT_MARK, body)
        if not allow_cut:  # every part after the first starts at a section heading
            for body in bodies[1:]:
                self.assertRegex(body, r"^##? ")
        return k, bodies

    # ---------------------------------------------------------------- the three fixture repos

    def test_small_repo_is_one_part_on_every_source(self):
        self.fixture(800, index_bytes=300, handoff_lines=10)
        for src in SOURCES:
            with self.subTest(source=src):
                k, bodies = self.check_lossless(src)
                self.assertEqual(k, 1)

    def test_30kb_memory_every_source(self):
        self.fixture(30_000)
        seen = {}
        for src in SOURCES:
            with self.subTest(source=src):
                k, bodies = self.check_lossless(src)
                seen[src] = (k, "".join(bodies))
        self.assertGreater(seen["startup"][0], 1)
        self.assertIn("CANARY-STATE", seen["startup"][1])
        self.assertIn("CANARY-STATE", seen["compact"][1])  # compact re-injects identity + memory
        self.assertNotIn("CANARY-STATE", seen["resume"][1])  # resume: nudges + stats only

    def test_60kb_memory_every_source(self):
        self.fixture(60_000)
        for src in SOURCES:
            with self.subTest(source=src):
                k, bodies = self.check_lossless(src)
                joined = "".join(bodies)
                if src in ("startup", "clear", "fork", "compact"):
                    self.assertIn("TRUNCATED — the cache is over its injection cap", joined)

    def test_parallel_runs_agree_on_the_session_counter(self):
        self.fixture(30_000)
        for _ in range(3):
            self.check_lossless("startup")
        with open(os.path.join(self.repo, ".claude", "state", "session_count")) as fh:
            self.assertEqual(fh.read().strip(), "3")

    def test_counter_printed_by_a_read_only_part_matches_part_one(self):
        """The stats block (with `session #N`) lands in part 2 here: 80 stale path refs fill the nudges.
        Part 2 runs in parallel with part 1, which bumps the counter — the race the protocol closes."""
        self.write(".claude/memory/MEMORY.md", "# Hot\n\n" + "".join(
            "- [2026-01-01] see `docs/missing-%03d-some-long-name.md` for x\n" % i for i in range(80)))
        for run in range(1, 6):
            k, bodies = self.check_lossless("startup")
            self.assertNotIn("=== SESSION START", bodies[0])
            self.assertIn("(session #%d) ===" % run, bodies[1])

    # ---------------------------------------------------------------- limits and edges

    def test_over_long_single_line_is_cut_with_a_marker_and_nothing_lost(self):
        self.fixture(5_000, long_line=25_000)
        k, bodies = self.check_lossless("startup", allow_cut=True)
        self.assertGreaterEqual(sum(b.count(CUT_MARK) for b in bodies), 2)
        self.assertIn("END-OF-LONG", "".join(bodies))

    def test_more_than_six_parts_warns_in_part_six(self):
        self.fixture(60_000, index_bytes=40_000)
        self.env["CMK_INJECT_BUDGET"] = "200000"
        printed = self.run_parts("startup")
        k, bodies = self.split(printed)
        self.assertGreater(k, 6)
        self.assertEqual(printed[6].rstrip("\n").splitlines()[-1], OVERFLOW)
        self.assertLessEqual(units(printed[6]), CAP)
        for n in range(1, 6):
            self.assertNotIn(OVERFLOW, printed[n])

    def test_part_past_the_last_prints_nothing(self):
        self.fixture(800, index_bytes=300, handoff_lines=10)
        printed = self.run_parts("startup")
        self.assertIsNotNone(printed[1])
        for n in range(2, 7):
            self.assertIsNone(printed[n])

    def test_parts_two_to_six_write_no_files(self):
        self.fixture(30_000)
        old = os.path.join(self.repo, ".claude", "state", "old-bookkeeping")
        self.write(".claude/state/old-bookkeeping", "x")
        os.utime(old, (1, 1))  # a prune candidate: only part 1 may delete it

        def snapshot():
            snap = {}
            for base, dirs, files in os.walk(self.repo):
                for name in dirs + files:
                    path = os.path.join(base, name)
                    st = os.lstat(path)
                    snap[path] = (st.st_size, st.st_mtime_ns)
            return snap

        before = snapshot()
        for src in SOURCES:
            self.run_parts(src, which=range(2, 7))
        self.assertEqual(snapshot(), before)
        self.run_parts("startup", which=[1])
        self.assertFalse(os.path.exists(old))

    def test_unadopted_repo_prints_one_part_and_writes_nothing(self):
        printed = self.run_parts("startup")
        k, bodies = self.split(printed)
        self.assertEqual(k, 1)
        self.assertIn("not set up in this repository", bodies[0])
        self.assertEqual(os.listdir(self.repo), [])

    # ---------------------------------------------------------------- wiring and the counter protocol

    def test_wiring_runs_six_parts_and_matches_max_parts(self):
        self.assertEqual(GROUP["matcher"], "startup|clear|resume|compact|fork")
        self.assertEqual(len(WIRINGS), 6)
        for n, cmd in enumerate(WIRINGS, start=1):
            self.assertTrue(cmd.endswith(" --part %d" % n), cmd)
        for hook in GROUP["hooks"]:
            self.assertEqual(hook.get("timeout"), 20)
        with open(SCRIPT, encoding="utf-8") as fh:
            self.assertRegex(fh.read(), r"(?m)^MAX_PARTS = 6$")

    def test_counter_protocol_read_only_peek(self):
        """A parallel part derives part 1's number whether it reads before or after part 1 wrote."""
        sys.dont_write_bytecode = True
        os.environ["CLAUDE_PROJECT_DIR"] = self.repo
        try:
            spec = importlib.util.spec_from_file_location("cmk_session_start_under_test", SCRIPT)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        self.write(".claude/state/session_count", "41")
        self.assertEqual(mod.peek_session_counter("s|startup"), 42)  # before part 1 wrote
        self.assertEqual(mod.bump_session_counter("s|startup"), 42)
        self.assertEqual(mod.peek_session_counter("s|startup"), 42)  # after
        self.assertEqual(mod.peek_session_counter("other|startup"), 43)  # the next session
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".claude", "state", ".session_count.tmp")))


if __name__ == "__main__":
    unittest.main(verbosity=1)
