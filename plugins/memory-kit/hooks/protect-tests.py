#!/usr/bin/env python3
"""PreToolUse(Edit|Write) — guard the test suite from being "fixed" instead of the code.

v6 rewrite. The v5 shell version blocked with exit 2, which had two failure modes found in
real use:

  * TDD was impossible. Creating a test with Write was allowed, but EVERY later Edit of that
    same file was hard-blocked — so the red→green loop could never run. v6 never blocks a file
    the agent created in this session (tracked in .claude/state/), and asks instead of refusing.
  * No escape hatch. A legitimate test refactor had to be done outside Claude Code. v6 emits
    `permissionDecision: "ask"` — the user decides in one keystroke — and honours
    CMK_ALLOW_TEST_EDITS=1 for a deliberate test-maintenance session.

The rule it enforces is unchanged and is the point of the hook: a failing test means the CODE
is wrong, not the test.

Output: {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                "permissionDecision": "ask"|"allow",
                                "permissionDecisionReason": "..."}}
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

TEST_PATH_RE = re.compile(
    r"(^|/)test_[^/]+\.py$"      # Python: test_foo.py
    r"|(^|/)[^/]+_test\.py$"     # Python: foo_test.py
    r"|(^|/)[^/]+_test\.go$"     # Go
    r"|/__tests__/"              # JS/TS convention
    r"|(^|/)tests?/"             # a tests/ or test/ directory segment
    r"|\.test\."                 # foo.test.ts
    r"|\.spec\."                 # foo.spec.ts
)

# Not code, never guarded — fixtures, docs and data under a tests/ dir are ordinary files.
EXEMPT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".snap", ".fixture"}


def allow() -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}))
    sys.exit(0)


def ask(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def session_created_file(project_dir: Path, session_id: str, file_path: str) -> bool:
    """Files this session created are its own to iterate on — that is the TDD loop."""
    ledger = project_dir / ".claude" / "state" / f"{session_id}_created_tests"
    if not ledger.exists():
        return False
    try:
        return file_path in ledger.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False


def remember_created(project_dir: Path, session_id: str, file_path: str) -> None:
    ledger = project_dir / ".claude" / "state" / f"{session_id}_created_tests"
    try:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(file_path + "\n")
    except OSError:
        pass


def main() -> None:
    if os.environ.get("CMK_ALLOW_TEST_EDITS") == "1":
        allow()

    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        allow()
        return

    file_path = str((payload.get("tool_input") or {}).get("file_path") or "")
    if not file_path:
        allow()

    if Path(file_path).suffix.lower() in EXEMPT_SUFFIXES:
        allow()
    if not TEST_PATH_RE.search(file_path):
        allow()

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
    session_id = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id") or "unknown")) or "unknown"

    # A new test file, or one this session authored: the red→green loop, always allowed.
    if not Path(file_path).exists():
        remember_created(project_dir, session_id, file_path)
        allow()
    if session_created_file(project_dir, session_id, file_path):
        allow()

    ask(
        f"{file_path} is an existing test file. A failing test usually means the CODE is wrong, "
        "not the test — confirm only if this edit is deliberate test maintenance (renaming, new "
        "coverage, a spec whose expectation genuinely changed). "
        "Set CMK_ALLOW_TEST_EDITS=1 for a whole session of test work."
    )


if __name__ == "__main__":
    main()
