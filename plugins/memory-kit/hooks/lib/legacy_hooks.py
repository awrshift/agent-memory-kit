"""Find project hooks that are copies of the kit's own (7.3) — read-only, never raises.

Repos adopted before the plugin copied the kit's hooks into `.claude/hooks/` and wired them in
`.claude/settings.json`; with the plugin installed both copies fire. A wired script counts as a copy only on a
POSITIVE signal in its CONTENT, under the event the kit hook runs on — never on its file name (a slimmed project
session-start.py is legitimate):

  PreCompact    emits `"decision": "block"` and names MEMORY.md
  SessionStart  reads `.claude/memory/MEMORY.md` (a path or a joined Path) and prints `additionalContext`
  SessionEnd    logs the kit's line `[hook] SessionEnd: session=`
  PreToolUse    a test-file guard: `Protect test files from modification`, `Test files are protected`,
                or `CMK_ALLOW_TEST_EDITS`

Skipped when the project's settings (`settings.local.json` over `settings.json`) disable the plugin.
Tests: hooks/tests/test_legacy_hooks.py. Python 3.9+, stdlib only.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

SETTINGS = (".claude/settings.json", ".claude/settings.local.json")
MAX_READ = 512 * 1024
MAX_LISTED = 8
SCRIPT_RE = re.compile(r"""[^\s"'`;|&()<>]+\.(?:sh|bash|py|js|mjs|cjs|ts)\b""")
MEMORY_PATH_RE = re.compile(
    r"""\.claude/memory/MEMORY\.md|["']\.claude["']\s*/\s*["']memory["']\s*/\s*["']MEMORY\.md["']"""
)
SIGNALS = {
    "PreCompact": ("pre-compact", "blocks compaction over MEMORY.md",
                   lambda t: re.search(r'"decision"\s*:\s*"block"', t) and "MEMORY.md" in t),
    "SessionStart": ("session-start", "reads MEMORY.md into the session context",
                     lambda t: MEMORY_PATH_RE.search(t) and "additionalContext" in t),
    "SessionEnd": ("session-end", "logs the session close",
                   lambda t: "[hook] SessionEnd: session=" in t),
    "PreToolUse": ("protect-tests", "guards test files",
                   lambda t: re.search(r"Protect test files from modification|Test files are protected|"
                                       r"CMK_ALLOW_TEST_EDITS", t)),
}


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def plugin_disabled(project_dir: Path) -> bool:
    state = None
    for rel in SETTINGS:  # local after shared: the later file wins
        plugins = _load(project_dir / rel).get("enabledPlugins")
        if isinstance(plugins, dict):
            for key, value in plugins.items():
                if str(key).split("@", 1)[0] == "memory-kit" and isinstance(value, bool):
                    state = value
    return state is False


def _scripts(command: str, project_dir: Path) -> list[Path]:
    text = re.sub(r"\$\{?CLAUDE_PROJECT_DIR\}?", str(project_dir), command)
    text = re.sub(r"\$\{?HOME\}?", str(Path.home()), text)
    found = []
    for token in SCRIPT_RE.findall(text):
        path = Path(os.path.expanduser(token))
        found.append(path if path.is_absolute() else project_dir / path)
    return found


def _read(path: Path) -> str:
    try:
        if not path.is_file():
            return ""
        with path.open(encoding="utf-8", errors="replace") as fh:
            return fh.read(MAX_READ)
    except OSError:
        return ""


def find_copies(project_dir: Path) -> list[tuple[str, str, str, str]]:
    """(settings file, event, script as written relative to the project, what the copy does) for each copy."""
    if plugin_disabled(project_dir):
        return []
    out = []
    for rel in SETTINGS:
        hooks = _load(project_dir / rel).get("hooks")
        if not isinstance(hooks, dict):
            continue
        for event, groups in hooks.items():
            if event not in SIGNALS or not isinstance(groups, list):
                continue
            _, what, matches = SIGNALS[event]
            for group in groups:
                handlers = group.get("hooks") if isinstance(group, dict) else None
                if not isinstance(handlers, list):
                    continue
                for handler in handlers:
                    command = handler.get("command") if isinstance(handler, dict) else None
                    if not isinstance(command, str):
                        continue
                    for script in _scripts(command, project_dir):
                        if matches(_read(script)):
                            try:
                                shown = str(script.relative_to(project_dir))
                            except ValueError:
                                shown = str(script)
                            out.append((rel, event, shown, what))
    return out


def legacy_hooks_hint(project_dir: Path) -> str:
    try:
        copies = find_copies(project_dir)
    except Exception:  # noqa: BLE001 — a nudge must never break session start
        return ""
    if not copies:
        return ""
    rows = "\n".join(
        f"  - `{rel}` {event} → `{script}` ({what})" for rel, event, script, what in copies[:MAX_LISTED]
    )
    more = f"\n  - …and {len(copies) - MAX_LISTED} more" if len(copies) > MAX_LISTED else ""
    return (
        "## ⚠ Project hooks that are copies of the kit's hooks\n\n"
        f"{len(copies)} hook(s) wired in this project's settings are copies of the kit's hooks — the plugin "
        f"already runs them, so each fires twice:\n{rows}{more}\n\n"
        "Remove those entries from the settings file (keep any project-only logic in a hook of its own), "
        "or disable the plugin for this project. Ask the user before editing settings.\n"
    )
