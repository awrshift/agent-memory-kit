#!/usr/bin/env python3
"""Session start flags a project that wires its own copy of a kit hook (AC-7, v7.3) — run:
python3 plugins/memory-kit/hooks/tests/test_legacy_hooks.py

Repos adopted before the plugin existed copied the kit's hooks into `.claude/hooks/` and wired them in
`.claude/settings.json`; with the plugin installed both fire (two PreCompact blocks, two SessionStart injections).
The detector (`hooks/lib/legacy_hooks.py`) reads the project's settings files, resolves each wired script and
flags it on a POSITIVE signal in its CONTENT, by event — never on its file name:
  PreCompact    emits `"decision": "block"` and names MEMORY.md
  SessionStart  READS `.claude/memory/MEMORY.md` and prints `additionalContext` (8.2: naming the path is not
                enough — a project hook that only stat()s the file for a size nudge is not a copy)
  SessionEnd    logs the kit's `[hook] SessionEnd: session=` line
  PreToolUse    a test-file guard (`Protect test files from modification`, `Test files are protected`,
                `CMK_ALLOW_TEST_EDITS`)
Skipped when the project's settings disable the plugin. Shown on startup and clear only.

Every case runs the EXACT SessionStart commands from hooks.json (all six parts) against a throwaway repo and
reads the injected text. What this proves: which wiring the nudge names on these fixtures. Its false-positive
count over the real adopter repos is a separate measurement (reported with the release). `ReadSignalBounds` calls
the SessionStart read signal directly and pins its caps (aliases collected, every quantifier bounded, the line cap) —
bounds, never a stopwatch.
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
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "hooks", "lib"))
import legacy_hooks  # noqa: E402

try:  # the regex parser: re._parser from Python 3.11, sre_parse before
    from re import _parser as sre_parse
except ImportError:  # pragma: no cover
    import sre_parse
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
SIZE_NUDGE_SESSION_START = '''"""Project-only context: the plan and a size nudge for the memory file."""
import json
from pathlib import Path
ROOT = Path(".")
MEMORY = ROOT / ".claude" / "memory" / "MEMORY.md"
SOFT_CAP = 16_000


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def size_nudge():
    try:
        size = MEMORY.stat().st_size
    except OSError:
        return ""
    return f"`.claude/memory/MEMORY.md` is {size} bytes: merge lines first." if size > SOFT_CAP else ""


print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                         "additionalContext": read(ROOT / "docs" / "plan.md") + size_nudge()}}))
'''
READ_FORMS = {
    "a read helper on a name": '''MEMORY_FILE = PROJECT_DIR / ".claude" / "memory" / "MEMORY.md"
def read_file_safe(path):
    return path.read_text()
print(json.dumps({"additionalContext": read_file_safe(MEMORY_FILE)}))
''',
    "open on the line": '''print(json.dumps({"additionalContext": open(".claude/memory/MEMORY.md").read()}))
''',
    "read_text after a joined path": '''body = (PROJECT_DIR / ".claude" / "memory" / "MEMORY.md").read_text()
print(json.dumps({"additionalContext": body}))
''',
    "shell cat of a variable": '''#!/bin/bash
MEMORY_FILE="$CLAUDE_PROJECT_DIR/.claude/memory/MEMORY.md"
BODY=$(cat "$MEMORY_FILE")
jq -n --arg c "$BODY" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $c}}'
''',
}
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

    def test_a_hook_that_only_stats_the_memory_file_is_not_flagged(self):
        """8.2: the path named next to `additionalContext`, the file only stat()ed for a size nudge, a read helper used
        on another file — project logic, not a copy (the pre-8.2 signal, «mentions the path», flagged it)."""
        self.write(".claude/hooks/session-start.py", SIZE_NUDGE_SESSION_START)
        self.settings(wired("SessionStart", "session-start.py", "python3"))
        self.assertNotIn(NUDGE, self.injected())

    def test_each_read_form_is_flagged(self):
        """A read of the memory file in each form a copy uses, plus the kit's own current session-start.py."""
        with open(os.path.join(PLUGIN_ROOT, "hooks", "session-start.py"), encoding="utf-8") as fh:
            forms = dict(READ_FORMS, **{"the kit's own hook": fh.read()})
        for label, body in forms.items():
            with self.subTest(form=label):
                script = "session-start.sh" if body.startswith("#!/bin/bash") else "session-start.py"
                self.write(".claude/hooks/" + script, body)
                self.settings(wired("SessionStart", script, "bash" if script.endswith(".sh") else "python3"))
                self.assertIn(NUDGE, self.injected())

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

    # ------------------------------------------------------------ R2-4: how the command names the script (v7.3 r2)

    def test_the_docs_recommended_quoting_is_resolved(self):
        """`"$CLAUDE_PROJECT_DIR"/.claude/hooks/x.sh` (the form the Claude Code hooks doc recommends) and the
        braced/unquoted forms resolve to the project's script."""
        self.write(".claude/hooks/pre-compact.sh", KIT_PRECOMPACT)
        for command in ('"$CLAUDE_PROJECT_DIR"/.claude/hooks/pre-compact.sh',
                        'bash "${CLAUDE_PROJECT_DIR}"/.claude/hooks/pre-compact.sh',
                        "bash $CLAUDE_PROJECT_DIR/.claude/hooks/pre-compact.sh",
                        "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/pre-compact.sh"):
            with self.subTest(command=command):
                self.settings({"PreCompact": [{"hooks": [{"type": "command", "command": command}]}]})
                text = self.injected()
                self.assertIn(NUDGE, text)
                self.assertIn(".claude/hooks/pre-compact.sh", text)

    def test_a_project_path_with_a_space(self):
        """A project directory with a space, every quoting form, plus a quoted relative path with a space."""
        spaced = os.path.join(self.repo, "my project")
        os.makedirs(spaced)
        self.addCleanup(shutil.rmtree, self.repo, True)
        self.repo, self.env["CLAUDE_PROJECT_DIR"] = spaced, spaced
        self.write(".claude/memory/MEMORY.md", "# Hot\n\n- [2026-01-01] CANARY\n")
        self.write(".claude/hooks/pre-compact.sh", KIT_PRECOMPACT)
        self.write(".claude/hooks/save memory.sh", KIT_PRECOMPACT)
        for command, shown in (('"$CLAUDE_PROJECT_DIR"/.claude/hooks/pre-compact.sh', "pre-compact.sh"),
                               ('bash "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-compact.sh"', "pre-compact.sh"),
                               ("bash '.claude/hooks/save memory.sh'", "save memory.sh")):
            with self.subTest(command=command):
                self.settings({"PreCompact": [{"hooks": [{"type": "command", "command": command}]}]})
                text = self.injected()
                self.assertIn(NUDGE, text)
                self.assertIn(".claude/hooks/" + shown, text)

    def test_worst_case_command_under_two_seconds(self):
        """A settings command is text the kit did not write: a 100,000-char word without a script extension (the
        pre-r2 findall was quadratic: 40,000 chars → 4.7 s, scratchpad evidence legacy-worst-case-before.txt)."""
        import time
        for label, command in (("long word", "a" * 100000), ("dots", "a." * 50000), ("separators", ";a" * 50000),
                               ("unbalanced quote", '"' + "a.s" * 30000)):
            with self.subTest(case=label):
                self.settings({"PreCompact": [{"hooks": [{"type": "command", "command": command}]}]})
                t0 = time.monotonic()
                self.assertNotIn(NUDGE, self.injected())
                self.assertLess(time.monotonic() - t0, 2.0, label)


MEM = ".claude/memory/MEMORY.md"


def repeats(pattern):
    """Every (min, max) repeat bound in a compiled pattern, nested groups and branches included."""
    found = []

    def walk(node):
        if isinstance(node, (list, tuple, sre_parse.SubPattern)):
            for item in node:
                walk(item)
        if isinstance(node, tuple) and len(node) == 2 and node[0] in (sre_parse.MAX_REPEAT, sre_parse.MIN_REPEAT):
            found.append(node[1][:2])

    walk(sre_parse.parse(pattern.pattern, pattern.flags))
    return found


class ReadSignalBounds(unittest.TestCase):
    """The SessionStart read signal runs on text the kit does not write, inside the session start's timeout (8.2 fix
    round 1: an unbounded `\\w*` around `read` grew with the square of a line's length, and one pattern per assigned
    name per line multiplied the work by the name count)."""

    def signal(self, text):
        return legacy_hooks.SIGNALS["SessionStart"][2]("additionalContext\n" + text)

    def test_every_pattern_of_the_read_signal_is_bounded(self):
        patterns = {"READ_BEFORE_RE": legacy_hooks.READ_BEFORE_RE, "READ_AFTER_RE": legacy_hooks.READ_AFTER_RE,
                    "ASSIGN_RE": legacy_hooks.ASSIGN_RE, "MEMORY_PATH_RE": legacy_hooks.MEMORY_PATH_RE,
                    "alias read": legacy_hooks._alias_read_re(["MEMORY_FILE", "MEM"])}
        for name, pattern in patterns.items():
            with self.subTest(pattern=name):
                bounds = repeats(pattern)
                self.assertTrue(bounds)
                self.assertEqual([b for b in bounds if b[1] == sre_parse.MAXREPEAT], [])
                self.assertLessEqual(max(b[1] for b in bounds), 200)  # the window

    def test_at_most_eight_aliases_and_one_pattern_for_them(self):
        self.assertEqual(legacy_hooks.MAX_ALIASES, 8)
        head = "".join('a%d = "%s"\n' % (i, MEM) for i in range(9))
        calls = []
        real = legacy_hooks._alias_read_re

        def counting(names):
            calls.append(names)
            return real(names)

        legacy_hooks._alias_read_re = counting
        try:
            self.assertTrue(self.signal(head + "ctx = a7.read_text()\n"))
            self.assertFalse(self.signal(head + "ctx = a8.read_text()\n"))  # the ninth name is never collected
        finally:
            legacy_hooks._alias_read_re = real
        self.assertEqual(len(calls), 2)  # one alternation per text, not one pattern per name
        self.assertEqual([len(names) for names in calls], [8, 8])

    def test_a_line_over_the_line_cap_is_skipped(self):
        line = "ctx = open(%r).read()" % MEM
        pad = " " * (legacy_hooks.MAX_LINE - len(line))
        self.assertTrue(self.signal(line + pad + "\n"))
        self.assertFalse(self.signal(line + pad + " \n"))

    def test_a_read_word_is_bounded(self):
        """`read` plus at most 40 word characters before `(`: a 4,000-char `read…read` word is no read call."""
        self.assertTrue(self.signal("ctx = read" + "x" * 40 + "(%r)\n" % MEM))
        self.assertFalse(self.signal("ctx = read" + "x" * 41 + "(%r)\n" % MEM))
        self.assertFalse(self.signal("read" * 990 + MEM + "\n"))

    def test_a_size_count_with_wc_is_not_a_read(self):
        """The shell twin of the stat-only case. A redirect (`wc -c < "$X"`) still counts as a read: a stated limit."""
        self.assertFalse(self.signal('MEM="$CLAUDE_PROJECT_DIR/%s"\nsize=$(wc -c "$MEM")\n' % MEM))
        self.assertFalse(self.signal('size=$(wc -c "$CLAUDE_PROJECT_DIR/%s")\n' % MEM))
        self.assertTrue(self.signal('MEM="$CLAUDE_PROJECT_DIR/%s"\nsize=$(wc -c < "$MEM")\n' % MEM))


if __name__ == "__main__":
    unittest.main(verbosity=1)
