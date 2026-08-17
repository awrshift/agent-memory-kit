#!/usr/bin/env python3
"""SessionStart hook — context injection via hookSpecificOutput.additionalContext.

v6.0 (plugin form). What changed vs v5 and WHY:

1. THE HOT CACHE IS ACTUALLY INJECTED.  v5 read MEMORY.md only to measure it, while
   CLAUDE.md claimed the file was "always loaded (hot path)". It was not: Claude Code
   auto-loads CLAUDE.md / .claude/rules/ and its own auto-memory directory — never
   <project>/.claude/memory/MEMORY.md. The ritual wrote to a file the agent never saw
   unless it happened to open it. This hook now injects the BODY.
2. THE PLUGIN'S IDENTITY DOC IS INJECTED.  A plugin cannot ship CLAUDE.md or rules, so
   the working agreement travels here, versioned with the plugin. Nothing to paste.
3. PROFILE PER SOURCE.  startup/clear/fork → full; compact → identity + memory only
   (that is the layer compaction drops); resume → nudges + stats (the transcript still
   carries the rest). v5 fired the full payload on all five.
4. NO SILENT WRITES.  v5 created MEMORY.md from a template on first run. A plugin can be
   installed user-wide, so an unadopted repository gets a one-line pointer to
   /memory-kit:setup instead of files it never asked for.
5. STATE IS PRUNED.  Per-session bookkeeping older than STATE_TTL_DAYS is deleted.

Output: {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parent.parent))

STATE_DIR = PROJECT_DIR / ".claude" / "state"
MEMORY_FILE = PROJECT_DIR / ".claude" / "memory" / "MEMORY.md"
INDEX_FILE = PROJECT_DIR / "knowledge" / "index.md"
HANDOFFS_DIR = PROJECT_DIR / "context" / "handoffs"
PROJECTS_DIR = PROJECT_DIR / "projects"
EXPERIMENTS_DIR = PROJECT_DIR / "experiments"

IDENTITY_FILE = PLUGIN_ROOT / "context" / "identity.md"
STALE_REFS_SCRIPT = PLUGIN_ROOT / "hooks" / "lib" / "stale-refs.py"
SESSION_FILE = STATE_DIR / "session_count"

# Budget covers the whole injection. Raised 20k → 48k in v6 because the memory body now
# travels with it; the old number was sized for a stats-only payload.
BUDGET = int(os.environ.get("CMK_INJECT_BUDGET", 48_000))

# Three independent MEMORY.md caps. Line count alone is not enough: content densifies
# into ever-longer lines while `wc -l` stays flat (a real production failure: 51.5 KB
# packed into 152 lines). Each cap catches a different shape.
MEMORY_LINE_CAP = int(os.environ.get("CMK_MEMORY_LINE_CAP", 180))
MEMORY_BYTE_CAP = int(os.environ.get("CMK_MEMORY_BYTE_CAP", 32_768))  # 32 KiB
MEMORY_MAX_LINE_CHARS = int(os.environ.get("CMK_MEMORY_MAXLINE_CAP", 3_000))

MEMORY_INJECT_CAP = 40_000  # a cache at its 32 KB cap fits whole; a bloated one truncates loudly
HANDOFF_INJECT_CAP = 6_000
STATE_TTL_DAYS = 30

# Stale-ref auto-check scope = the always-loaded layer only.
HOT_MEMORY_TARGETS = ["CLAUDE.md", ".claude/memory/MEMORY.md"]

FULL_SOURCES = {"startup", "clear", "fork"}
RESTORE_SOURCES = {"compact"}


def read_hook_input() -> dict:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def age_days(path: Path) -> int | None:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    return int((datetime.now(timezone.utc).timestamp() - mtime) / 86400)


def human_age(days: int | None) -> str:
    if days is None:
        return "unknown"
    if days == 0:
        return "today"
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def is_adopted() -> bool:
    """Has this repository actually adopted the kit? A user-wide plugin install must not
    assume it — and must never scaffold files into a repo that never asked."""
    return MEMORY_FILE.exists() or HANDOFFS_DIR.exists()


def adoption_pointer() -> str:
    return (
        "## Memory Kit — not set up in this repository\n\n"
        "The `memory-kit` plugin is installed but this repo has no `.claude/memory/MEMORY.md` "
        "and no `context/handoffs/`. Nothing was created automatically.\n\n"
        "Run `/memory-kit:setup` to scaffold the memory layers here (it asks before writing), "
        "or ignore this line if this repository is not meant to carry kit memory.\n"
    )


def prune_state() -> None:
    """Per-session bookkeeping accumulated forever in v5. Keep the directory bounded."""
    if not STATE_DIR.exists():
        return
    cutoff = time.time() - STATE_TTL_DAYS * 86400
    for path in STATE_DIR.iterdir():
        if path.name in {".gitkeep", "session_count"} or not path.is_file():
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


def memory_cap_breaches(content: str) -> list[str]:
    lines = content.splitlines()
    reasons: list[str] = []
    if len(lines) > MEMORY_LINE_CAP:
        reasons.append(f"lines = {len(lines)} (cap {MEMORY_LINE_CAP})")
    byte_count = len(content.encode("utf-8"))
    if byte_count > MEMORY_BYTE_CAP:
        reasons.append(f"size = {byte_count / 1024:.1f} KB (cap {MEMORY_BYTE_CAP // 1024} KB)")
    max_line = max((len(ln) for ln in lines), default=0)
    if max_line > MEMORY_MAX_LINE_CHARS:
        reasons.append(
            f"longest line = {max_line} chars (cap {MEMORY_MAX_LINE_CHARS}) "
            "— likely a stacked chronicle in one line"
        )
    return reasons


def maybe_caps_prompt(content: str | None) -> str:
    if content is None:
        return ""
    reasons = memory_cap_breaches(content)
    if not reasons:
        return ""
    reason_block = "\n".join(f"  - {r}" for r in reasons)
    return (
        "## ⚠ MEMORY DISCIPLINE TRIGGER\n\n"
        f"MEMORY.md tripped {len(reasons)} of 3 caps:\n{reason_block}\n\n"
        "Run `/memory-kit:memory-audit` BEFORE other work: it classifies every section, proposes a "
        "move plan for approval, promotes settled patterns to `knowledge/concepts/`, drops what "
        "already lives in a handoff, and replaces the header with fresh current-state lines.\n"
    )


def maybe_stale_refs_hint() -> str:
    """Nudge when the always-loaded layer references files that no longer exist.

    The #1 memory failure is stale beliefs — memory asserting paths that changed on disk.
    Deterministic detect-half; non-blocking, never auto-deletes.
    """
    if not STALE_REFS_SCRIPT.exists():
        return ""
    try:
        result = subprocess.run(
            ["python3", str(STALE_REFS_SCRIPT), *HOT_MEMORY_TARGETS],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return ""
    match = re.search(r"(\d+) unresolved", result.stdout)
    if not match or int(match.group(1)) == 0:
        return ""
    detail = "\n".join(
        ln for ln in result.stdout.splitlines() if ln.startswith("✗") or ln.strip().startswith("L")
    )
    return (
        "## ⚠ Stale memory references\n\n"
        f"{match.group(1)} path reference(s) in memory no longer resolve on disk:\n\n"
        f"{detail}\n\n"
        "Verify each (renamed? moved? deleted?) and update or remove the entry.\n"
    )


def bump_session_counter() -> int:
    """Counts real sessions only — v5 also counted resumes and post-compact restarts."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    current = 0
    if SESSION_FILE.exists():
        try:
            current = int(SESSION_FILE.read_text(encoding="utf-8").strip() or "0")
        except (ValueError, OSError):
            current = 0
    new = current + 1
    try:
        SESSION_FILE.write_text(str(new), encoding="utf-8")
    except OSError:
        pass
    return new


def list_dirs(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted(
        (p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def build_stats(session_num: int | None, content: str | None) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    counter = f" (session #{session_num})" if session_num is not None else ""
    lines = [f"=== SESSION START — {today}{counter} ===", "", "## Memory"]

    if content is not None:
        mem_lines_list = content.splitlines()
        mem_bytes = len(content.encode("utf-8"))
        mem_max_line = max((len(ln) for ln in mem_lines_list), default=0)
        capacity = min(100, len(mem_lines_list) * 100 // MEMORY_LINE_CAP)
        days = age_days(MEMORY_FILE)
        stale = " !! STALE" if days is not None and days >= 5 else ""
        lines.append(
            f"MEMORY.md: {len(mem_lines_list)}/{MEMORY_LINE_CAP} lines ({capacity}% full), "
            f"{mem_bytes / 1024:.1f} KB / {MEMORY_BYTE_CAP // 1024} KB cap, "
            f"max-line {mem_max_line} / {MEMORY_MAX_LINE_CHARS} cap — updated {human_age(days)}{stale}"
        )
    else:
        lines.append("No MEMORY.md found")
    lines.append("")

    projects = list_dirs(PROJECTS_DIR)
    if projects:
        lines.append("## Projects")
        lines += [f"- projects/{p.name}/ — touched {human_age(age_days(p))}" for p in projects[:6]]
        lines.append("")

    experiments = list_dirs(EXPERIMENTS_DIR)
    if experiments:
        lines.append("## Experiments")
        for e in experiments[:6]:
            days = age_days(e)
            flag = "  ⚠ open 30+ days — close or revive?" if days is not None and days >= 30 else ""
            lines.append(f"- experiments/{e.name}/ — touched {human_age(days)}{flag}")
        lines.append("")

    lines.append("## Git")
    try:
        branch = subprocess.run(
            ["git", "-C", str(PROJECT_DIR), "branch", "--show-current"],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(PROJECT_DIR), "status", "--short"],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip()
        if branch:
            lines.append(f"branch: {branch}")
        tracked = [ln for ln in status.splitlines() if not ln.startswith("??")] if status else []
        lines.append(
            f"working tree: {len(tracked)} tracked change(s)"
            + (" (clean — only untracked files)" if not tracked else "")
        )
        if status:
            lines.append("\n".join(status.splitlines()[:5]))
    except (subprocess.SubprocessError, OSError):
        lines.append("(git unavailable)")

    return "\n".join(lines)


def newest_handoff() -> Path | None:
    if not HANDOFFS_DIR.exists():
        return None
    files = [p for p in HANDOFFS_DIR.glob("*.md") if p.name != "HANDOFF-TEMPLATE.md"]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def build_context(source: str) -> str:
    if not is_adopted():
        return adoption_pointer()

    prune_state()
    full = source in FULL_SOURCES
    restore = source in RESTORE_SOURCES

    content: str | None = read_file_safe(MEMORY_FILE) if MEMORY_FILE.exists() else None
    if not content:
        content = None

    parts: list[str] = []
    remaining = BUDGET

    def add_section(title: str, body: str) -> None:
        nonlocal remaining
        if not body.strip():
            return
        chunk = f"## {title}\n\n{body.rstrip()}\n"
        if len(chunk) > remaining:
            if remaining > 500:
                parts.append(chunk[: remaining - 40].rstrip() + "\n\n…(truncated — read the file)\n")
                remaining = 0
            return
        parts.append(chunk)
        remaining -= len(chunk)

    def add_raw(body: str) -> None:
        nonlocal remaining
        if not body.strip():
            return
        parts.append(body.rstrip() + "\n")
        remaining = max(0, remaining - len(body) - 1)

    # 1. The working agreement. A plugin cannot ship CLAUDE.md, so it travels here —
    #    and this is exactly the layer compaction drops, hence also on `compact`.
    if full or restore:
        add_raw(read_file_safe(IDENTITY_FILE))

    # 2. Discipline nudges — the agent must see them before it starts working.
    if not restore:
        for hint in (maybe_caps_prompt(content), maybe_stale_refs_hint()):
            add_raw(hint)

    # 3. Stats. The session counter counts sessions, not hook runs.
    if not restore:
        add_raw(build_stats(bump_session_counter() if full else None, content))

    # 4. THE HOT CACHE ITSELF (the v5 bug: measured, never injected).
    if content is not None and (full or restore):
        body = content
        if len(body) > MEMORY_INJECT_CAP:
            body = body[:MEMORY_INJECT_CAP].rstrip() + (
                "\n\n…(TRUNCATED — the cache is over its injection cap; run "
                "`/memory-kit:close-session` and prune)\n"
            )
        add_section("MEMORY.md (hot cache — durable patterns + current state)", body)
    elif content is None and full:
        add_section(
            "MEMORY.md",
            "Empty — no hot cache yet. Capture this session's durable observations as "
            "`[YYYY-MM-DD]`-prefixed lines.",
        )

    # 5. Where we left off.
    hand = newest_handoff()
    if hand is not None and full:
        body = read_file_safe(hand)
        if len(body) > HANDOFF_INJECT_CAP:
            body = body[:HANDOFF_INJECT_CAP].rstrip() + "\n\n…(truncated — read the full file on demand)\n"
        add_section(
            f"Latest handoff — context/handoffs/{hand.name} (updated {human_age(age_days(hand))})",
            body,
        )
    elif hand is not None and restore:
        add_section("Latest handoff", f"`context/handoffs/{hand.name}` — read it if you need the thread.")
    elif full:
        add_section(
            "Latest handoff",
            "No handoffs yet. `/memory-kit:close-session` writes the first one at the end of this session.",
        )

    # 6. The cheap pointer layer.
    if full:
        add_section("Knowledge Base Index", read_file_safe(INDEX_FILE))

    return "\n---\n\n".join(parts).rstrip() + "\n"


def main() -> None:
    payload = read_hook_input()
    source = str(payload.get("source") or "startup")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": build_context(source),
        }
    }
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
