#!/usr/bin/env python3
"""system-audit :: «gates actually hold» — prove each PreToolUse hook through its EXACT wiring.

For every PreToolUse hook command in ~/.claude/settings.json, <project>/.claude/settings.json,
<project>/.claude/settings.local.json and this plugin's hooks/hooks.json, pipe a known-bad sample
through the exact command string (a shell, CLAUDE_PROJECT_DIR / CLAUDE_PLUGIN_ROOT exported, plus the
`env` blocks those settings files give every session):

  Bash        -> `git push --force origin x`
  Edit|Write  -> an Edit (or Write) that changes an assertion line of an existing test file

PASS = exit 2, or JSON `permissionDecision` deny/ask. Exit 1 is a FAIL: Claude Code treats it as a
non-blocking error and the tool call goes through. A hook guarding a different danger (e.g. only
pushes to one remote) FAILs this sample legitimately — the per-tool verdict is the finding: does ANY
hook stop the sample? Also reported: python3 missing, broad allows, root env files without a Read deny.

Read-only on the audited repo (the test-file sample comes from `git ls-files` or a temp dir).
Usage: python3 gates.py [project_dir]      exit 1 when a tool that has hooks lets its sample through.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parents[3])
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "lib"))
import rails  # noqa: E402

TEST_PATH_RE = re.compile(r"(^|/)test_[^/]+\.py$|(^|/)[^/]+_test\.(py|go)$|/__tests__/|(^|/)tests?/|\.test\.|\.spec\.")
CODE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rb")
ASSERT_RE = re.compile(r"expect\(|assert|toBe|toEqual|toThrow")
BAD_COMMAND = "git push --force origin x"


def hook_sources(project: Path):
    """(label, settings dict or hooks.json dict) — every place a PreToolUse hook can be declared."""
    home = Path.home() / ".claude" / "settings.json"
    yield "user " + str(home), rails.load_settings(home)
    for name in ("settings.json", "settings.local.json"):
        path = project / ".claude" / name
        yield "project " + str(path.relative_to(project)), rails.load_settings(path)
    yield "plugin hooks/hooks.json", rails.load_settings(PLUGIN_ROOT / "hooks" / "hooks.json")


def session_env(project: Path):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project), CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT))
    notes = []
    for path in (Path.home() / ".claude" / "settings.json", project / ".claude" / "settings.json",
                 project / ".claude" / "settings.local.json"):
        block = rails.load_settings(path).get("env")
        if isinstance(block, dict):
            for key, value in block.items():
                env[str(key)] = str(value)
                if key in ("CMK_ALLOW_TEST_EDITS", "CMK_GIT_GUARD"):
                    notes.append("%s=%s is set by %s (`env`) — it switches a kit hook off in every session" % (key, value, path))
    for key in ("CMK_ALLOW_TEST_EDITS", "CMK_GIT_GUARD"):
        if key in os.environ and not any(n.startswith(key + "=") for n in notes):
            notes.append("%s=%s is set in the auditor's shell" % (key, os.environ[key]))
    return env, notes


def matches(matcher, tool):
    if matcher in (None, "", "*"):
        return True
    try:
        return re.fullmatch(matcher, tool) is not None
    except re.error:
        return matcher == tool


def test_file_sample(project: Path, scratch: Path):
    """(path, one assertion line) — a tracked test file of the project, else a temp one."""
    try:
        files = subprocess.run(["git", "-C", str(project), "ls-files"], capture_output=True, text=True,
                               timeout=10).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        files = []
    for rel in files:
        if not (TEST_PATH_RE.search(rel) and rel.endswith(CODE_SUFFIXES)):
            continue
        path = project / rel
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if ASSERT_RE.search(line) and len(line) < 300:
                    return path, line
        except OSError:
            continue
    path = scratch / "tests" / "test_gate_probe.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("def test_total():\n    assert total() == 5\n", encoding="utf-8")
    return path, "    assert total() == 5"


def payload_for(tool, project: Path, sample):
    base = {"session_id": "cmk-gates-probe", "hook_event_name": "PreToolUse", "cwd": str(project),
            "tool_name": tool}
    if tool == "Bash":
        base["tool_input"] = {"command": BAD_COMMAND, "description": "gate probe"}
    else:
        path, line = sample
        weaker = line + "  # weakened"
        if tool == "Edit":
            base["tool_input"] = {"file_path": str(path), "old_string": line, "new_string": weaker}
        else:
            content = path.read_text(encoding="utf-8", errors="replace").replace(line, weaker, 1)
            base["tool_input"] = {"file_path": str(path), "content": content}
    return base


def verdict(proc):
    if proc.returncode == 2:
        return "PASS", "exit 2: " + proc.stderr.strip().splitlines()[0][:100] if proc.stderr.strip() else "exit 2"
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            out = json.loads(proc.stdout)
            decision = (out.get("hookSpecificOutput") or {}).get("permissionDecision")
        except ValueError:
            decision = None
        if decision in ("deny", "ask"):
            return "PASS", "permissionDecision=" + decision
    if proc.returncode == 1:
        return "FAIL", "exit 1 = non-blocking error, the call goes through: " + (proc.stderr.strip()[:80] or "-")
    return "FAIL", "exit %d, no deny/ask" % proc.returncode


def main():
    project = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
    scratch = Path(tempfile.mkdtemp(prefix="cmk-gates-"))
    env, notes = session_env(project)
    print("# Gates actually hold — %s\n" % project)
    py = shutil.which("python3")
    print("python3: %s" % (py or "MISSING — every python3 hook below fails as a non-blocking error"))
    for note in notes:
        print("note: " + note)
    print()
    print("| source | matcher | tool | result | evidence | command |")
    print("|---|---|---|---|---|---|")
    per_tool = {}
    sample = None
    try:
        for label, cfg in hook_sources(project):
            for group in (cfg.get("hooks") or {}).get("PreToolUse") or []:
                matcher = group.get("matcher")
                tools = [t for t in ("Bash", "Edit", "Write") if matches(matcher, t)]
                for hook in group.get("hooks") or []:
                    cmd = hook.get("command") or ""
                    if hook.get("type", "command") != "command" or not tools:
                        print("| %s | %s | — | SKIP | not a command hook on Bash/Edit/Write | `%s` |" % (label, matcher, cmd[:60]))
                        continue
                    for tool in tools:
                        if tool != "Bash" and sample is None:
                            sample = test_file_sample(project, scratch)
                        payload = json.dumps(payload_for(tool, project, sample))
                        try:
                            proc = subprocess.run(cmd, shell=True, input=payload, capture_output=True, text=True,
                                                  env=env, cwd=str(project), timeout=hook.get("timeout") or 60)
                            result, evidence = verdict(proc)
                        except subprocess.TimeoutExpired:
                            result, evidence = "FAIL", "timed out (Claude Code lets the call through)"
                        per_tool.setdefault(tool, []).append(result == "PASS")
                        print("| %s | %s | %s | %s | %s | `%s` |" % (
                            label, matcher, tool, result, evidence.replace("|", "/"), cmd.replace("|", "\\|")[:90]))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print()
    exit_code = 0
    for tool in ("Bash", "Edit", "Write"):
        results = per_tool.get(tool)
        if not results:
            print("- %s: no PreToolUse hook — nothing but permissions stands in front of it" % tool)
        elif any(results):
            print("- %s: HOLDS — %d of %d hooks stop the sample" % (tool, sum(results), len(results)))
        else:
            print("- %s: OPEN — %d hook(s), none stops the sample" % (tool, len(results)))
            exit_code = 1
    if sample:
        print("  (test-file sample: %s)" % sample[0])
    perms = rails.load_permissions(project)
    broad = rails.broad_allows(perms)
    uncovered = rails.uncovered_env_files(project, perms)
    print("\nBroad allows (resolve before the auto-mode classifier): %s" % (", ".join(broad) or "none"))
    print("Root env files without a Read deny: %s" % (", ".join(uncovered) or "none"))
    print("Context size (not scripted): claude -p --output-format json \"Reply with exactly: OK\" "
          "→ input + cache creation + cache read tokens, on a clean tree")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
