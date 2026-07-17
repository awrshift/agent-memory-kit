#!/usr/bin/env python3
"""SessionStart hook — context injection via hookSpecificOutput.additionalContext.

v5.0 (lean core): injects, in priority order —
    1. Memory-discipline nudges, only when they fire: the three MEMORY.md caps
       (lines / bytes / longest line) + stale file references.
    2. Session stats: MEMORY.md size vs caps, projects/experiments overview, git state.
    3. The newest session handoff from context/handoffs/ (your "where we left off").
    4. knowledge/index.md (the catalog of deep memory).

Retired in v5.0: NSP + daily-log injection (the daily-chronicle layer moved to
.kit/advanced/close-day-layer/ — see .kit/CHANGELOG.md).

Output: {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parent.parent.parent))
STATE_DIR = PROJECT_DIR / ".claude" / "state"
MEMORY_FILE = PROJECT_DIR / ".claude" / "memory" / "MEMORY.md"
MEMORY_TEMPLATE = PROJECT_DIR / ".claude" / "memory" / "MEMORY-TEMPLATE.md"
INDEX_FILE = PROJECT_DIR / "knowledge" / "index.md"
HANDOFFS_DIR = PROJECT_DIR / "context" / "handoffs"
PROJECTS_DIR = PROJECT_DIR / "projects"
EXPERIMENTS_DIR = PROJECT_DIR / "experiments"
STALE_REFS_SCRIPT = PROJECT_DIR / ".claude" / "memory" / "scripts" / "stale-refs.py"
SESSION_FILE = STATE_DIR / "session_count"

DEFAULT_BUDGET = 20_000
BUDGET = int(os.environ.get("CMK_INJECT_BUDGET", DEFAULT_BUDGET))

# Three independent MEMORY.md caps. Line count alone is not enough: content can
# densify into ever-longer lines while `wc -l` stays flat (a real production
# failure: 51.5 KB packed into 152 lines). Each cap catches a different shape.
# Tunable via env (kept from PR #2).
MEMORY_LINE_CAP = int(os.environ.get("CMK_MEMORY_LINE_CAP", 180))
MEMORY_BYTE_CAP = int(os.environ.get("CMK_MEMORY_BYTE_CAP", 32_768))  # 32 KiB
MEMORY_MAX_LINE_CHARS = int(os.environ.get("CMK_MEMORY_MAXLINE_CAP", 3_000))  # «giant single-line chronicle» guard

HANDOFF_INJECT_CAP = 6_000

# Stale-ref auto-check scope = the always-loaded layer only.
HOT_MEMORY_TARGETS = ["CLAUDE.md", ".claude/memory/MEMORY.md"]


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


def ensure_memory_file() -> None:
    """MEMORY.md is gitignored (personal data stays private even if the repo is
    pushed), so a fresh clone has none — create it from the committed template."""
    if MEMORY_FILE.exists() or not MEMORY_TEMPLATE.exists():
        return
    try:
        MEMORY_FILE.write_text(MEMORY_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    except OSError:
        pass


def maybe_caps_prompt() -> str:
    """Active prompt when MEMORY.md trips ANY of the three caps."""
    if not MEMORY_FILE.exists():
        return ""
    try:
        content = MEMORY_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""

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
            f"longest line = {max_line} chars (cap {MEMORY_MAX_LINE_CHARS}) — likely a stacked chronicle in one line"
        )
    if not reasons:
        return ""

    reason_block = "\n".join(f"  - {r}" for r in reasons)
    return (
        "## ⚠ MEMORY DISCIPLINE TRIGGER\n\n"
        f"MEMORY.md tripped {len(reasons)} of 3 caps:\n{reason_block}\n\n"
        "Run the `/close-session` audit BEFORE other work: promote settled patterns to "
        "`knowledge/concepts/`, drop absorbed ones, and REPLACE the header with fresh "
        "current-state lines. The header is «current state», never a chronicle.\n"
    )


def maybe_stale_refs_hint() -> str:
    """Nudge when the always-loaded layer references files that no longer exist.

    The #1 memory failure is stale beliefs — memory asserting paths/facts that
    changed on disk. Deterministic detect-half; non-blocking.
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
        "Verify each (renamed? moved? deleted?) and update/remove the entry.\n"
    )


def bump_session_counter() -> int:
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


def build_stats(session_num: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"=== SESSION START — {today} (hook run #{session_num}) ===", ""]

    lines.append("## Memory")
    content = None
    if MEMORY_FILE.exists():
        try:
            content = MEMORY_FILE.read_text(encoding="utf-8")
        except OSError:
            content = None
    if content is not None:
        mem_lines_list = content.splitlines()
        mem_lines = len(mem_lines_list)
        mem_bytes = len(content.encode("utf-8"))
        mem_max_line = max((len(ln) for ln in mem_lines_list), default=0)
        capacity = min(100, mem_lines * 100 // MEMORY_LINE_CAP)
        days = age_days(MEMORY_FILE)
        stale = " !! STALE" if days is not None and days >= 5 else ""
        lines.append(
            f"MEMORY.md: {mem_lines}/{MEMORY_LINE_CAP} lines ({capacity}% full), "
            f"{mem_bytes / 1024:.1f} KB / {MEMORY_BYTE_CAP // 1024} KB cap, "
            f"max-line {mem_max_line} / {MEMORY_MAX_LINE_CHARS} cap — updated {human_age(days)}{stale}"
        )
    else:
        lines.append("No MEMORY.md found")
    lines.append("")

    projects = list_dirs(PROJECTS_DIR)
    if projects:
        lines.append("## Projects")
        for p in projects[:6]:
            lines.append(f"- projects/{p.name}/ — touched {human_age(age_days(p))}")
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


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def build_context() -> str:
    ensure_memory_file()
    session_num = bump_session_counter()
    parts: list[str] = []
    remaining = BUDGET

    def add_section(title: str, body: str) -> None:
        nonlocal remaining
        if not body.strip():
            return
        chunk = f"## {title}\n\n{body.rstrip()}\n"
        if len(chunk) > remaining:
            if remaining > 500:
                parts.append(chunk[: remaining - 20].rstrip() + "\n\n...(truncated)\n")
                remaining = 0
            return
        parts.append(chunk)
        remaining -= len(chunk)

    # Discipline nudges first (agent must see them before anything else).
    for hint in (maybe_caps_prompt(), maybe_stale_refs_hint()):
        if hint:
            parts.append(hint + "\n")
            remaining = max(0, remaining - len(hint) - 1)

    # Session stats (always).
    stats = build_stats(session_num)
    parts.append(stats + "\n")
    remaining = max(0, remaining - len(stats) - 1)

    # Newest handoff — "where we left off". Replaces the v4 NSP injection.
    hand = newest_handoff()
    if hand is not None:
        body = read_file_safe(hand)
        if len(body) > HANDOFF_INJECT_CAP:
            body = body[:HANDOFF_INJECT_CAP].rstrip() + "\n\n…(truncated — read the full file on demand)\n"
        days = age_days(hand)
        add_section(f"Latest handoff — context/handoffs/{hand.name} (updated {human_age(days)})", body)
    else:
        add_section(
            "Latest handoff",
            "No handoffs yet — first session. `/close-session` writes the first one at the end of this session.",
        )

    # Knowledge index (the cheap pointer layer).
    add_section("Knowledge Base Index", read_file_safe(INDEX_FILE))

    return "\n---\n\n".join(parts).rstrip() + "\n"


def main() -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": build_context(),
        }
    }
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
