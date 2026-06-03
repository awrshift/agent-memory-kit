#!/usr/bin/env python3
"""Usage telemetry aggregator.

Parses Claude Code session transcripts in ~/.claude/projects/<encoded>/**/*.jsonl
and writes knowledge/usage-frequency.md — a frequency profile of which files,
skills, and tools you actually use.

The point: it turns "what can I archive / what's dead weight?" from a guess into
data. Files read a lot recently = hot (load-bearing). Files with zero reads in
30 days = cold candidates (safe to archive or prune). The agent surfaces the cold
list at /close-day and proposes archival — you say yes, the agent writes.

Filters mechanical reads (auto-loaded paths like MEMORY.md / CLAUDE.md, which the
session-start hook loads for you) and collapses bursts (multi-edit on a single
task), so it measures deliberate use, not noise. See usage_config.py to tune.

Read-only signal — it writes one report and touches nothing else. It does not
violate the "user only talks, agent writes" invariant.

Manual invocation:
    python3 .claude/memory/scripts/aggregate_usage.py
"""

from __future__ import annotations

import fnmatch
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[3]
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
ENCODED_PATH = str(PROJECT_DIR).replace("/", "-")
SESSIONS_DIR = CLAUDE_PROJECTS_DIR / ENCODED_PATH
OUTPUT = PROJECT_DIR / "knowledge" / "usage-frequency.md"

sys.path.insert(0, str(Path(__file__).parent))
from usage_config import (  # noqa: E402
    BURST_THRESHOLD,
    BURST_WINDOW_MINUTES,
    MECHANICAL_PATHS,
    TOP_BASH_COMMANDS,
    TOP_COLD_CANDIDATES,
    TOP_EDITS,
    TOP_HOT_FILES,
    TOP_SKILLS,
    TOP_TOOLS,
)


def is_mechanical(path: str) -> bool:
    if not path:
        return False
    return any(fnmatch.fnmatch(path, pat) for pat in MECHANICAL_PATHS)


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_events(d: dict) -> list[dict]:
    """Extract tool_use events from one JSONL message dict."""
    if d.get("type") != "assistant":
        return []
    content = d.get("message", {}).get("content", [])
    if not isinstance(content, list):
        return []
    timestamp = d.get("timestamp", "")

    events = []
    for c in content:
        if not (isinstance(c, dict) and c.get("type") == "tool_use"):
            continue
        name = c.get("name", "?")
        inp = c.get("input", {}) or {}
        target = ""
        if name in ("Read", "Edit", "Write", "NotebookEdit"):
            target = inp.get("file_path", "") or ""
        elif name == "Skill":
            target = inp.get("skill", "") or ""
        elif name == "Bash":
            cmd = (inp.get("command", "") or "").strip().split()
            target = cmd[0] if cmd else ""
        elif name in ("Grep",):
            target = inp.get("pattern", "") or ""
        elif name == "Glob":
            target = inp.get("pattern", "") or ""
        elif name == "WebFetch":
            target = inp.get("url", "") or ""
        events.append({"tool": name, "target": target, "timestamp": timestamp})
    return events


def deduplicate_bursts(events: list[dict]) -> list[dict]:
    """For each (tool, target), collapse clusters of > BURST_THRESHOLD events
    within BURST_WINDOW_MINUTES into BURST_THRESHOLD."""
    by_key: dict[tuple[str, str], list[tuple[datetime, dict]]] = defaultdict(list)
    no_ts = []
    for e in events:
        dt = parse_iso(e.get("timestamp", ""))
        if dt is None:
            no_ts.append(e)
            continue
        by_key[(e["tool"], e["target"])].append((dt, e))

    burst_window = timedelta(minutes=BURST_WINDOW_MINUTES)
    out = list(no_ts)
    for evts in by_key.values():
        evts.sort(key=lambda x: x[0])
        cluster_start: datetime | None = None
        cluster_count = 0
        for dt, e in evts:
            if cluster_start is None or (dt - cluster_start) > burst_window:
                cluster_start = dt
                cluster_count = 1
                out.append(e)
            else:
                cluster_count += 1
                if cluster_count <= BURST_THRESHOLD:
                    out.append(e)
    return out


def aggregate(events: list[dict]) -> dict:
    """Compute per-(tool, target) frequency stats."""
    now = datetime.now(timezone.utc)
    stats: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"30d": 0, "all": 0, "first": None, "last": None}
    )
    for e in events:
        dt = parse_iso(e.get("timestamp", ""))
        if dt is None:
            continue
        key = (e["tool"], e["target"])
        s = stats[key]
        s["all"] += 1
        if (now - dt).days <= 30:
            s["30d"] += 1
        if s["first"] is None or dt < s["first"]:
            s["first"] = dt
        if s["last"] is None or dt > s["last"]:
            s["last"] = dt
    return stats


def fmt_age(dt: datetime | None, now: datetime) -> str:
    if dt is None:
        return "—"
    days = (now - dt).days
    if days == 0:
        return "today"
    if days == 1:
        return "1d ago"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 7}w ago"
    return f"{days // 365}y ago"


def short_path(p: str, max_len: int = 70) -> str:
    if len(p) <= max_len:
        return p
    return "…" + p[-(max_len - 1) :]


def render_report(stats: dict, now: datetime, total_events: int, after_burst: int) -> str:
    by_tool: Counter = Counter()
    reads, edits, skills_used, bash_cmds = [], [], [], []

    for (tool, target), s in stats.items():
        by_tool[tool] += s["all"]
        mech = tool == "Read" and is_mechanical(target)
        entry = {
            "target": target or "<empty>",
            "30d": s["30d"],
            "all": s["all"],
            "last": fmt_age(s["last"], now),
            "first": fmt_age(s["first"], now),
            "mechanical": mech,
        }
        if tool == "Read" and not mech:
            reads.append(entry)
        elif tool in ("Edit", "Write", "NotebookEdit") and not is_mechanical(target):
            edits.append(entry)
        elif tool == "Skill":
            skills_used.append(entry)
        elif tool == "Bash":
            bash_cmds.append(entry)

    reads.sort(key=lambda x: -x["30d"])
    edits.sort(key=lambda x: -x["30d"])
    skills_used.sort(key=lambda x: -x["all"])
    bash_cmds.sort(key=lambda x: -x["all"])
    cold = sorted(
        [r for r in reads if r["30d"] == 0],
        key=lambda x: 999 if x["last"] == "—" else 0,
    )

    lines = [
        "# Usage Frequency Report",
        "",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `~/.claude/projects/{ENCODED_PATH}/**/*.jsonl`",
        f"**Events:** {total_events:,} tool_use → {after_burst:,} after burst-collapse",
        f"**Filter:** mechanical-paths blacklist + burst (> {BURST_THRESHOLD} same key in {BURST_WINDOW_MINUTES} min → 1 use)",
        "",
        "> ⚠ **Frequency ≠ value.** A cold concept may be foundational, just rarely re-read.",
        "> Use the cold list as ONE input to a `/close-day` archival proposal, not an auto-delete trigger.",
        "",
        "## Tool surface (all-time)",
        "",
        "| Tool | Calls |",
        "|------|------:|",
    ]
    for tool, n in by_tool.most_common(TOP_TOOLS):
        lines.append(f"| {tool} | {n:,} |")

    lines += ["", f"## Top {TOP_HOT_FILES} hot files (Read, 30d)", ""]
    if reads:
        lines += ["| File | 30d | all | last |", "|------|----:|----:|------|"]
        for r in reads[:TOP_HOT_FILES]:
            lines.append(f"| `{short_path(r['target'])}` | {r['30d']} | {r['all']} | {r['last']} |")
    else:
        lines.append("_no non-mechanical Read events_")

    lines += ["", f"## Top {TOP_COLD_CANDIDATES} cold candidates (0 reads in 30d)", ""]
    if cold:
        lines += ["| File | all-time | last used |", "|------|---------:|-----------|"]
        for r in cold[:TOP_COLD_CANDIDATES]:
            lines.append(f"| `{short_path(r['target'])}` | {r['all']} | {r['last']} |")
    else:
        lines.append("_no cold candidates_")

    lines += ["", f"## Top {TOP_EDITS} edits (30d)", ""]
    if edits:
        lines += ["| File | 30d | all | last |", "|------|----:|----:|------|"]
        for r in edits[:TOP_EDITS]:
            lines.append(f"| `{short_path(r['target'])}` | {r['30d']} | {r['all']} | {r['last']} |")
    else:
        lines.append("_no edit events_")

    lines += ["", "## Skill invocations", ""]
    if skills_used:
        lines += ["| Skill | calls | last |", "|-------|------:|------|"]
        for r in skills_used[:TOP_SKILLS]:
            lines.append(f"| `{r['target']}` | {r['all']} | {r['last']} |")
    else:
        lines.append("_no Skill tool calls in dataset_")

    lines += ["", f"## Top {TOP_BASH_COMMANDS} bash commands (by first word)", ""]
    if bash_cmds:
        lines += ["| Command | calls | last |", "|---------|------:|------|"]
        for r in bash_cmds[:TOP_BASH_COMMANDS]:
            lines.append(f"| `{r['target']}` | {r['all']} | {r['last']} |")
    else:
        lines.append("_no Bash events_")

    lines += [
        "",
        "---",
        "",
        "*Generated by `.claude/memory/scripts/aggregate_usage.py`. Manual invocation only.*",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if not SESSIONS_DIR.exists():
        print(f"ERROR: {SESSIONS_DIR} not found.", file=sys.stderr)
        print("No session transcripts yet — work a few sessions first, then re-run.", file=sys.stderr)
        return 1

    files = list(SESSIONS_DIR.rglob("*.jsonl"))
    print(f"Parsing {len(files)} JSONL files…", file=sys.stderr)

    all_events: list[dict] = []
    json_errors = 0
    for f in files:
        try:
            with open(f) as fh:
                for line in fh:
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        json_errors += 1
                        continue
                    all_events.extend(extract_events(d))
        except OSError:
            continue

    if json_errors:
        print(f"  json errors skipped: {json_errors}", file=sys.stderr)

    total = len(all_events)
    print(f"  tool_use events: {total:,}", file=sys.stderr)
    deduped = deduplicate_bursts(all_events)
    print(f"  after burst-collapse: {len(deduped):,}", file=sys.stderr)

    stats = aggregate(deduped)
    now = datetime.now(timezone.utc)
    report = render_report(stats, now, total, len(deduped))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(report.splitlines())} lines)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
