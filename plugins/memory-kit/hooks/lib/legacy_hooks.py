"""Find project hooks that are copies of the kit's own (7.3) — read-only, never raises.

Repos adopted before the plugin copied the kit's hooks into `.claude/hooks/` and wired them in
`.claude/settings.json`; with the plugin installed both copies fire. A wired script counts as a copy only on a
POSITIVE signal in its CONTENT, under the event the kit hook runs on — never on its file name (a slimmed project
session-start.py is legitimate):

  PreCompact    emits `"decision": "block"` and names MEMORY.md
  SessionStart  READS `.claude/memory/MEMORY.md` (a path or a joined Path) and prints `additionalContext` — a read is
                a read call on the line that names the path, or on a name assigned that path (`X.read_text()`,
                `open(X)`, `read_file(X)`, `cat "$X"`); a hook that only `stat()`s the file is not a copy (8.2)
  SessionEnd    logs the kit's line `[hook] SessionEnd: session=`
  PreToolUse    a test-file guard: `Protect test files from modification`, `Test files are protected`,
                or `CMK_ALLOW_TEST_EDITS`

SessionStart limits (8.2). Reads it misses (none is in a real kit copy: every historical kit session-start.py reads
through `MEMORY_FILE.read_text(` or `read_file_safe(MEMORY_FILE)`): a keyword argument (`read_file_safe(path=X)`), a
wrapped name (`open(os.fspath(X))`), an assignment wrapped over lines, `subprocess.run(["cat", X])`, a `python3 -c`
one-liner on `"$X"`, a path held in a dict, a read of a name past the first MAX_ALIASES assigned the path. Flagged
though not a read: a redirect into a size count (`wc -c < "$X"` — the `<` counts, `wc` itself is no read word); the
path in a message on a line that also reads another file, or in a comment after a read word; a call such as
`start_thread(` on the path line; a short name assigned the path and later reused for another file. Missed by the
pattern bounds (8.2 fix round 1; no historical kit copy uses one): a read word over 40 characters past `read`
(`read_memory_file_contents_with_fallback_and_cache(X)`), a gap of more than 8 spaces or tabs where a pattern allows
one (`open(         X)`, `export` and 9 spaces), an assigned name over 61 characters, an assignment indented over 40
columns or annotated over 200 characters.

Bounds at the input (8.2 fix round 2): the SessionStart signal examines only the first READ_SIGNAL_TEXT characters
(64 KB) of a script — a read or an `additionalContext` placed after them is not seen; at most MAX_SCRIPTS_PER_EVENT
(8) script paths are read per event, over both settings files in the order written, the rest skipped — a copy wired
as the 9th script of its event is not flagged. The other events' signals read a script up to MAX_READ (512 KB).

Skipped when the project's settings (`settings.local.json` over `settings.json`) disable the plugin.
Tests: hooks/tests/test_legacy_hooks.py. Python 3.9+, stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from pathlib import Path

SETTINGS = (".claude/settings.json", ".claude/settings.local.json")
MAX_READ = 512 * 1024
MAX_LISTED = 8
# The two bounds at the input of the copy check (8.2 fix round 2: the work grew with whatever text and however many
# scripts a project wires). The SessionStart signal examines the first 64 KB (characters) of a script: the kit's own
# session-start.py is under 40 KB in every version (38,079 bytes at most in the kit's git history), so a copy reads
# the memory file inside it. At most 8 scripts are read per event; each of the six session-start parts runs this check.
READ_SIGNAL_TEXT = 64 * 1024
MAX_SCRIPTS_PER_EVENT = 8
SCRIPT_RE = re.compile(r"""[^\s"'`;|&()<>]+\.(?:sh|bash|py|js|mjs|cjs|ts)\b""")
PIECE_SPLIT_RE = re.compile(r"""[\s"'`;|&()<>]+""")
SCRIPT_WORD_RE = re.compile(r"""[^"'`;|&()<>]+\.(?:sh|bash|py|js|mjs|cjs|ts)""")  # one shell word: spaces allowed
PROJECT_TOKEN = "\x00cmk-project-dir\x00"  # stand-ins without spaces or quotes, replaced after the split
HOME_TOKEN = "\x00cmk-home\x00"
MEMORY_PATH_RE = re.compile(
    r"""\.claude/memory/MEMORY\.md|["']\.claude["'][ \t]{0,8}/[ \t]{0,8}["']memory["'][ \t]{0,8}/[ \t]{0,8}"""
    r"""["']MEMORY\.md["']"""
)
# A read of the memory file (8.2: the mention alone flagged a project hook that stat()s it for a size nudge): a read
# call or a shell read command before the path on its line (within 200 chars), a read call right after it, or the same
# on a name the line assigns the path to. Text the kit does not write, so every quantifier is bounded (a read word at
# most 40 word chars past `read`, space runs at most 8, windows 200 chars), lines over MAX_LINE are skipped, at most
# MAX_ALIASES names are collected and their reads are ONE alternation searched over the text once (8.2 fix round 1:
# `\b\w*read\w*(` backtracked quadratically in a long word, and one pattern per name per line multiplied the work).
SHELL_READ = r"\b(?:cat|head|tail|grep|sed|awk|jq)\b"
CALL_READ = r"(?:\bopen|[Rr]ead\w{0,40})[ \t]{0,8}\("
READ_BEFORE_RE = re.compile(
    rf"(?:{CALL_READ}[^\n]{{0,200}}|{SHELL_READ}[^|;&\n]{{0,200}}|<[ \t]{{0,8}}[\w{{}}/.\-\"'$]{{0,200}})$"
)
READ_AFTER_RE = re.compile(r"^[\"')\s]{0,4}\.(?:read_text|read_bytes|read|open)[ \t]{0,8}\(")
ASSIGN_RE = re.compile(
    r"^[ \t]{0,40}(?:(?:export|local|readonly|const|let|var)[ \t]{1,8})?([A-Za-z_]\w{0,60})[ \t]{0,8}"
    r"(?::[^=\n]{0,200})?=(?!=)"
)
MAX_ALIASES = 8
MAX_LINE = 4000


def _alias_read_re(names: list[str]) -> re.Pattern:
    """One pattern for a read of any of the names (at most MAX_ALIASES), searched once over the joined lines."""
    n = "(?:" + "|".join(map(re.escape, names)) + ")"
    return re.compile(
        rf"\b{n}\b[ \t]{{0,8}}\)?[ \t]{{0,8}}\.(?:read_text|read_bytes|read|open)[ \t]{{0,8}}\(|"
        rf"{CALL_READ}[ \t]{{0,8}}(?:str[ \t]{{0,8}}\([ \t]{{0,8}})?{n}\b|"
        rf"(?:{SHELL_READ}[^|;&\n]{{0,200}}|<[ \t]{{0,8}}[\"']?)\$\{{?{n}\b"
    )


def reads_memory(text: str) -> bool:
    """True when the text reads the memory file: a read on a line that names its path, or a read of a name that line
    assigns the path to (the first MAX_ALIASES such names). A mention with only `stat()` / `exists()` / a message is
    not a read. Only the first READ_SIGNAL_TEXT characters are examined."""
    lines = [line for line in text[:READ_SIGNAL_TEXT].splitlines() if len(line) <= MAX_LINE]
    aliases: list[str] = []
    for line in lines:
        match = MEMORY_PATH_RE.search(line)
        if not match:
            continue
        if READ_BEFORE_RE.search(line[: match.start()]) or READ_AFTER_RE.search(line[match.end():]):
            return True
        if len(aliases) < MAX_ALIASES:
            assigned = ASSIGN_RE.match(line)
            if assigned and assigned.end() <= match.start() and assigned.group(1) not in aliases:
                aliases.append(assigned.group(1))
    return bool(aliases) and _alias_read_re(aliases).search("\n".join(lines)) is not None


SIGNALS = {
    "PreCompact": ("pre-compact", "blocks compaction over MEMORY.md",
                   lambda t: re.search(r'"decision"\s*:\s*"block"', t) and "MEMORY.md" in t),
    "SessionStart": ("session-start", "reads MEMORY.md into the session context",
                     lambda t: "additionalContext" in t[:READ_SIGNAL_TEXT] and reads_memory(t)),
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
    """The script paths a hook command names (7.3 r2): `$CLAUDE_PROJECT_DIR` / `${CLAUDE_PROJECT_DIR}` (and `$HOME`),
    quoted or not, stand for their directory, then the command is split like a POSIX shell (shlex), so
    `"$CLAUDE_PROJECT_DIR"/.claude/hooks/x.sh` and a quoted path with a space resolve whole. A word that is not a
    script path itself (`bash -c 'python3 x.py'`) is searched for one, per separator-free piece; an unbalanced quote
    falls back to that search over the whole command. Linear in the command's length (7.3 r2: measured, see
    tests/test_legacy_hooks.py)."""
    text = re.sub(r"\$(?:CLAUDE_PROJECT_DIR\b|\{CLAUDE_PROJECT_DIR\})", PROJECT_TOKEN, command)
    text = re.sub(r"\$(?:HOME\b|\{HOME\})", HOME_TOKEN, text)
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>")
        lexer.whitespace_split = True
        words = list(lexer)
    except ValueError:
        words = [text]
    found = []
    project, home = str(project_dir), str(Path.home())
    for word in words:
        if "\x00" in word:
            word = word.replace(PROJECT_TOKEN, project).replace(HOME_TOKEN, home)
        if SCRIPT_WORD_RE.fullmatch(word):
            tokens = [word]
        else:  # one anchored match per separator-free piece: linear (findall restarts at every char — quadratic)
            tokens = [m.group(0) for m in map(SCRIPT_RE.match, PIECE_SPLIT_RE.split(word)) if m]
        for token in tokens:
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
    """(settings file, event, script as written relative to the project, what the copy does) for each copy. At most
    MAX_SCRIPTS_PER_EVENT script paths are read per event, over both settings files; the rest are skipped."""
    if plugin_disabled(project_dir):
        return []
    out = []
    read: dict[str, int] = {}  # scripts read per event
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
                    if read.get(event, 0) >= MAX_SCRIPTS_PER_EVENT:
                        break
                    command = handler.get("command") if isinstance(handler, dict) else None
                    if not isinstance(command, str):
                        continue
                    for script in _scripts(command, project_dir)[: MAX_SCRIPTS_PER_EVENT - read.get(event, 0)]:
                        read[event] = read.get(event, 0) + 1
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
