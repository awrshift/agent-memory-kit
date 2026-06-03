#!/usr/bin/env python3
"""
SessionStart hook — context injection via hookSpecificOutput.additionalContext.

Adapted from coleam00/claude-memory-compiler hooks/session-start.py (Karpathy's
knowledge-base pattern) with Memory Kit v3 extensions: MEMORY stats, projects,
experiments, git status baked into the injected context.

The hook prints a single JSON object to stdout:
    {
      "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "..."
      }
    }

Budget: default 50K chars (configurable via CMK_INJECT_BUDGET env var).
Priority order when truncating:
    1. Session stats (MEMORY, projects, experiments, git)
    2. knowledge/index.md (full)
    3. Latest daily/YYYY-MM-DD.md
    4. Second-latest daily log
    5. Top 3 recently-modified knowledge/concepts/*.md
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parent.parent.parent))
STATE_DIR = PROJECT_DIR / ".claude" / "state"
MEMORY_FILE = PROJECT_DIR / ".claude" / "memory" / "MEMORY.md"
KNOWLEDGE_DIR = PROJECT_DIR / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "index.md"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"
DAILY_DIR = PROJECT_DIR / "daily"
PROJECTS_DIR = PROJECT_DIR / "projects"
EXPERIMENTS_DIR = PROJECT_DIR / "experiments"
SESSION_FILE = STATE_DIR / "session_count"

DEFAULT_BUDGET = 50_000
BUDGET = int(os.environ.get("CMK_INJECT_BUDGET", DEFAULT_BUDGET))
TOP_CONCEPTS_COUNT = 3


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


def build_stats(session_num: int) -> str:
    lines = [f"=== SESSION START (#{session_num}) ===", ""]

    # Memory
    lines.append("## Memory")
    if MEMORY_FILE.exists():
        content = MEMORY_FILE.read_text(encoding="utf-8")
        mem_lines = len(content.splitlines())
        capacity = min(100, mem_lines * 100 // 200)
        knowledge_count = 0
        if KNOWLEDGE_DIR.exists():
            knowledge_count = sum(1 for _ in KNOWLEDGE_DIR.rglob("*.md"))
        days = age_days(MEMORY_FILE)
        stale = " !! STALE" if days is not None and days >= 5 else ""
        lines.append(
            f"MEMORY.md: {mem_lines}/200 lines ({capacity}% full) — updated {human_age(days)}{stale}"
        )
        lines.append(f"Knowledge wiki: {knowledge_count} articles")
        if mem_lines > 200:
            lines.append(
                f"⚠ MEMORY.md is over 200 lines ({mem_lines}). Run /close-day to promote settled "
                "patterns into knowledge/concepts/ (or .claude/rules/) and prune what's already absorbed."
            )
    else:
        lines.append("No MEMORY.md found")
    lines.append("")

    # Projects
    lines.append("## Projects")
    found_projects = False
    if PROJECTS_DIR.exists():
        for project_dir in sorted(PROJECTS_DIR.iterdir()):
            if not project_dir.is_dir():
                continue
            backlog = project_dir / "BACKLOG.md"
            if not backlog.exists():
                continue
            found_projects = True
            try:
                content = backlog.read_text(encoding="utf-8")
            except OSError:
                continue
            active = sum(
                1
                for line in content.splitlines()
                if "Status:" in line and any(s in line for s in ("IN PROGRESS", "TODO", "BLOCKED"))
            )
            completed = sum(1 for line in content.splitlines() if line.startswith("- **T-"))
            days = age_days(backlog)
            stale = f" !! STALE ({days} days)" if days is not None and days >= 5 else ""
            lines.append(f"- {project_dir.name}: {active} active, {completed} completed{stale}")
    if not found_projects:
        lines.append("No projects yet")
    lines.append("")

    # Experiments
    lines.append("## Experiments")
    exp_count = 0
    if EXPERIMENTS_DIR.exists():
        for exp_dir in sorted(EXPERIMENTS_DIR.iterdir()):
            if not exp_dir.is_dir():
                continue
            exp_file = exp_dir / "EXPERIMENT.md"
            if not exp_file.exists():
                continue
            exp_count += 1
            try:
                first_lines = exp_file.read_text(encoding="utf-8").splitlines()[:10]
            except OSError:
                first_lines = []
            status = ""
            for line in first_lines:
                if "Status:" in line:
                    status = line.split("Status:")[-1].strip().strip("*").strip()
                    break
            lines.append(f"- {exp_dir.name}{': ' + status if status else ''}")
    if exp_count == 0:
        lines.append("No active experiments")
    lines.append("")

    # Git
    lines.append("## Git")
    try:
        branch = subprocess.run(
            ["git", "-C", str(PROJECT_DIR), "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(PROJECT_DIR), "status", "--short"],
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
        if branch:
            lines.append(f"branch: {branch}")
        if status:
            short_status = "\n".join(status.splitlines()[:5])
            lines.append(short_status)
    except (subprocess.SubprocessError, OSError):
        lines.append("(git unavailable)")
    lines.append("")

    lines.append("=== Read context/next-session-prompt.md for full context ===")
    return "\n".join(lines)


def read_index() -> str:
    if not INDEX_FILE.exists():
        return ""
    try:
        return INDEX_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""


def find_recent_dailies(limit: int = 2) -> list[Path]:
    if not DAILY_DIR.exists():
        return []
    today = datetime.now(timezone.utc).astimezone()
    dailies = []
    for offset in range(14):
        date = today - timedelta(days=offset)
        path = DAILY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        if path.exists():
            dailies.append(path)
        if len(dailies) >= limit:
            break
    return dailies


def find_top_concepts(limit: int = 3) -> list[Path]:
    if not CONCEPTS_DIR.exists():
        return []
    concepts = list(CONCEPTS_DIR.glob("*.md"))
    concepts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return concepts[:limit]


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def build_context() -> str:
    """Assemble additionalContext payload honoring BUDGET."""
    session_num = bump_session_counter()
    parts: list[str] = []
    remaining = BUDGET

    def add_section(title: str, body: str) -> bool:
        nonlocal remaining
        if not body.strip():
            return False
        chunk = f"## {title}\n\n{body.rstrip()}\n"
        if len(chunk) > remaining:
            if remaining > 500:
                truncated = chunk[: remaining - 20].rstrip() + "\n\n...(truncated)\n"
                parts.append(truncated)
                remaining = 0
            return False
        parts.append(chunk)
        remaining -= len(chunk)
        return True

    # 1. Session stats (always included)
    stats = build_stats(session_num)
    parts.append(stats + "\n")
    remaining = max(0, remaining - len(stats) - 1)

    # 2. Knowledge index
    add_section("Knowledge Base Index", read_index())

    # 3. Recent daily logs (latest first)
    dailies = find_recent_dailies(limit=2)
    for daily in dailies:
        add_section(f"Daily Log — {daily.stem}", read_file_safe(daily))

    # 4. Top recent concepts
    for concept in find_top_concepts(limit=TOP_CONCEPTS_COUNT):
        rel = concept.relative_to(KNOWLEDGE_DIR)
        add_section(f"Recent Concept — {rel}", read_file_safe(concept))

    return "\n---\n\n".join(parts).rstrip() + "\n"


def main() -> None:
    context = build_context()
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
