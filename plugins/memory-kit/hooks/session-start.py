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
6. PARTS (7.2).  Claude Code caps one hook's additionalContext at 10,000 characters; over it the
   model gets a file path and a 2,000-char preview, so before 7.2 MEMORY.md never reached it.
   hooks.json runs this script MAX_PARTS times with `--part N`; each run builds the same full text,
   splits it at section boundaries into parts of <= PART_LIMIT and prints part N. Only part 1
   writes (state pruning, the session counter); parts 2..N are read-only. No flag = the whole
   text in one output (tests, tools, a manual look).

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
LIB_DIR = PLUGIN_ROOT / "hooks" / "lib"
SESSION_FILE = STATE_DIR / "session_count"
# `<session_id>|<source>\t<n>`, written by part 1 BEFORE session_count: a parallel part 2..6 that reads
# session_count first and this file second always derives the number part 1 printed.
SESSION_LAST_FILE = STATE_DIR / "session_last"

# The transport. Claude Code caps a hook's additionalContext at 10,000 chars (code.claude.com/docs/en/hooks);
# a part is packed to PART_LIMIT, leaving room for the one-line wrapper and the overflow line.
# MAX_PARTS must equal the number of `--part N` commands in hooks.json (a test holds them together).
MAX_PARTS = 6
PART_LIMIT = 9_500
PART_HEADER = "Memory Kit context — part {n} of {k} (parts arrive in any order; together they are the whole).\n"
OVERFLOW_LINE = (
    "Memory Kit: context exceeds 6 parts — the rest is NOT loaded; read .claude/memory/MEMORY.md now "
    "and run /memory-kit:memory-audit."
)
LINE_CUT_MARK = " […line continues in the next part]\n"
SECTION_START_RE = re.compile(r"\n(?=##? )")

# Budget covers the whole injection. Raised 20k → 48k in v6 because the memory body now
# travels with it; the old number was sized for a stats-only payload.
BUDGET = int(os.environ.get("CMK_INJECT_BUDGET", 48_000))

# Three independent MEMORY.md caps. Line count alone is not enough: content densifies
# into ever-longer lines while `wc -l` stays flat (a real production failure: 51.5 KB
# packed into 152 lines). Each cap catches a different shape.
MEMORY_LINE_CAP = int(os.environ.get("CMK_MEMORY_LINE_CAP", 180))
MEMORY_BYTE_CAP = int(os.environ.get("CMK_MEMORY_BYTE_CAP", 32_768))  # 32 KiB
MEMORY_MAX_LINE_CHARS = int(os.environ.get("CMK_MEMORY_MAXLINE_CAP", 3_000))

# Session-headed blocks: a heading named after a session or a date is a chronicle stacking up in
# the hot cache — the narrative belongs to the handoff, the lesson under a topic heading. A tag
# inside ( ) or [ ] is provenance on a topic heading ("Engine track (s37, 2026-08-17)"), not a
# session block; the current-state header may name its session. Measured 2026-09-25 over 23
# kit projects: 7 blocks flagged, 0 false flags (the 7.0.2 changelog carries the table).
SESSION_TAG_RE = re.compile(
    r"(?-i:\bs\d{1,3}\b)|\bsession[ -]?#?\d+|(?<!\w)сесси[яиюей]\s?#?\d+", re.IGNORECASE
)
DATED_HEADING_RE = re.compile(
    r"^(?:(?:findings|notes|log|updates?|wrap(?:-?up)?|итоги|заметки)\b)?\W*\d{4}-\d{2}-\d{2}",
    re.IGNORECASE,
)
CURRENT_STATE_RE = re.compile(r"^(?:current state|текущее состояние)\b", re.IGNORECASE)
BRACKETED_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")
SESSION_BLOCK_LIST_MAX = 5

MEMORY_INJECT_CAP = 40_000  # a cache at its 32 KB cap fits whole; a bloated one truncates loudly
HANDOFF_INJECT_CAP = 6_000
STATE_TTL_DAYS = 30

# A spec left in `building` for this long is either done-but-unmarked or abandoned; both are
# a lie in the project's plans/ folder. Surfaced at session start, never auto-corrected.
SPEC_STALE_DAYS = int(os.environ.get("CMK_SPEC_STALE_DAYS", 14))
SPEC_HEAD_LINES = 30  # the status/created header lives at the top; never read a whole spec
SPEC_STATUS_RE = re.compile(r"\*\*Status:?\*\*:?\s*([A-Za-z][A-Za-z-]*)")
SPEC_CREATED_RE = re.compile(r"\*\*Created:?\*\*:?\s*(\d{4}-\d{2}-\d{2})")
# 7.0.3: repos that keep specs in their own shape — a plain `Status: done (…) · Tier: …` line, no
# `Created:` — are read too. Plain labels count only at a line start or after a `·`, so prose in
# the first 30 lines ("the status: unclear") never parses as a header; the date then comes from
# the kit's `YYYY-MM-DD-<slug>.md` file name.
PLAIN_STATUS_RE = re.compile(r"(?:^|·)[ \t]*Status:[ \t]*([A-Za-z][A-Za-z-]*)", re.MULTILINE)
PLAIN_CREATED_RE = re.compile(r"(?:^|·)[ \t]*Created:[ \t]*(\d{4}-\d{2}-\d{2})", re.MULTILINE)
FILENAME_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
# A repo-level spec folder, read beside projects/*/plans/ (a repo without the kit's projects/ layer).
ROOT_PLANS_DIR = PROJECT_DIR / "docs" / "plans"

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
        # rails-v2 / rails-declined are decisions, not bookkeeping: pruning them would
        # bring the rails nudge back 30 days after the user answered it.
        if path.name in {".gitkeep", "session_count", "session_last", "rails-v2", "rails-declined"} or not path.is_file():
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


def session_block_headings(content: str) -> list[tuple[int, str]]:
    """(line number, heading) for every `##`–`####` heading named after a session or a date.

    Fenced code is skipped — a `## ` line inside a shell block is not a heading.
    """
    found: list[tuple[int, str]] = []
    in_fence = False
    for num, line in enumerate(content.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        heading = re.match(r"#{2,4}\s+(.*)", line)
        if in_fence or not heading:
            continue
        text = heading.group(1).strip()
        if CURRENT_STATE_RE.match(text):
            continue
        if SESSION_TAG_RE.search(BRACKETED_RE.sub(" ", text)) or DATED_HEADING_RE.match(text):
            found.append((num, line.strip()))
    return found


def maybe_session_block_hint(content: str | None) -> str:
    """Nudge, never block: close-session says «never a chronicle», and the files grew them anyway."""
    if content is None:
        return ""
    found = session_block_headings(content)
    if not found:
        return ""
    shown = "\n".join(
        f"  - L{num}: `{text[:100]}{'…' if len(text) > 100 else ''}`"
        for num, text in found[:SESSION_BLOCK_LIST_MAX]
    )
    more = f"\n  - …and {len(found) - SESSION_BLOCK_LIST_MAX} more" if len(found) > SESSION_BLOCK_LIST_MAX else ""
    return (
        "## ⚠ Session-headed blocks in MEMORY.md\n\n"
        f"{len(found)} heading(s) name a session or a date instead of a topic:\n{shown}{more}\n\n"
        "Dissolve them by topic at the next `/memory-kit:close-session` (or `/memory-kit:memory-audit`, "
        "mark `session-block`): a settled lesson → one line under its topic heading or a concept "
        "article; the session narrative → drop, the handoff already has it.\n"
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


def maybe_rails_hint() -> str:
    """One line when the permission rails look open (7.1). Read-only, no subprocess, never raises."""
    try:
        sys.dont_write_bytecode = True
        if str(LIB_DIR) not in sys.path:
            sys.path.insert(0, str(LIB_DIR))
        import rails

        line = rails.rails_line(PROJECT_DIR)
    except Exception:  # noqa: BLE001 — a nudge must never break session start
        return ""
    return line + "\n" if line else ""


def read_session_count() -> int:
    try:
        return int(SESSION_FILE.read_text(encoding="utf-8").strip() or "0")
    except (ValueError, OSError):
        return 0


def write_atomic(path: Path, text: str) -> None:
    """A parallel reader sees the old file or the new one, never a torn write."""
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def bump_session_counter(session_key: str | None) -> int:
    """Counts real sessions only — v5 also counted resumes and post-compact restarts. Part 1 only."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    new = read_session_count() + 1
    if session_key:
        write_atomic(SESSION_LAST_FILE, f"{session_key}\t{new}")
    write_atomic(SESSION_FILE, str(new))
    return new


def peek_session_counter(session_key: str | None) -> int:
    """The number part 1 prints, derived read-only by a part running in parallel with it.

    Read order is the proof: session_count first, session_last second. Part 1 writes them in the
    opposite order, so a session_last that is not ours yet means the count we read is the old one.
    """
    count = read_session_count()
    if session_key:
        try:
            key, _, num = SESSION_LAST_FILE.read_text(encoding="utf-8").rpartition("\t")
            if key == session_key:
                return int(num)
        except (ValueError, OSError):
            pass
    return count + 1


def list_dirs(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted(
        (p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def spec_flags(plans_dir: Path) -> tuple[int, int]:
    """(assumed specs, `building` specs older than SPEC_STALE_DAYS) in one plans folder.

    Non-recursive, stdlib only, header lines only — the stats block must stay cheap. Any
    unreadable or unparsable file is skipped: a malformed spec must never break the hook.
    """
    assumed = stale = 0
    try:
        paths = sorted(plans_dir.glob("*.md"))
    except OSError:
        return 0, 0
    for path in paths:
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                head = "".join(line for _, line in zip(range(SPEC_HEAD_LINES), handle))
        except OSError:
            continue
        status_match = SPEC_STATUS_RE.search(head) or PLAIN_STATUS_RE.search(head)
        if not status_match:
            continue
        status = status_match.group(1).lower()
        if status == "assumed":
            assumed += 1
        elif status == "building":
            created_match = (
                SPEC_CREATED_RE.search(head)
                or PLAIN_CREATED_RE.search(head)
                or FILENAME_DATE_RE.match(path.name)
            )
            if not created_match:
                continue
            try:
                created = datetime.strptime(created_match.group(1), "%Y-%m-%d")
            except ValueError:
                continue
            if (datetime.now() - created).days > SPEC_STALE_DAYS:
                stale += 1
    return assumed, stale


def spec_flag_text(plans_dir: Path) -> str:
    """` · N specs assumed … · M building > 14 d`, or "" — a zero count prints nothing."""
    assumed, stale = spec_flags(plans_dir)
    text = ""
    if assumed:
        text += f" · {assumed} spec{'s' if assumed != 1 else ''} assumed (owed ratification)"
    if stale:
        text += f" · {stale} building > {SPEC_STALE_DAYS} d"
    return text


def project_line(project: Path) -> str:
    """One stats row. A zero count prints nothing — the line stays quiet until it matters."""
    return (
        f"- projects/{project.name}/ — touched {human_age(age_days(project))}"
        + spec_flag_text(project / "plans")
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
        lines += [project_line(p) for p in projects[:6]]
        lines.append("")

    root_flags = spec_flag_text(ROOT_PLANS_DIR) if ROOT_PLANS_DIR.is_dir() else ""
    if root_flags:
        lines += ["## Plans", f"- docs/plans/ — {root_flags[len(' · '):]}", ""]

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
    # memory-audit wrote its deferred list here before 7.0.1; it is not a session handoff.
    files = [
        p
        for p in HANDOFFS_DIR.glob("*.md")
        if p.name != "HANDOFF-TEMPLATE.md" and not p.name.startswith("memory-audit-deferred-")
    ]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def build_context(source: str, writer: bool = True, session_key: str | None = None) -> str:
    """The whole injection. `writer=False` (parts 2..N) builds the same text without touching disk."""
    if not is_adopted():
        rails_hint = maybe_rails_hint()
        return adoption_pointer() + (f"\n{rails_hint}" if rails_hint else "")

    if writer:
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
        # The agent's shell does not expand ${CLAUDE_PLUGIN_ROOT}: hand it the real path.
        add_raw(read_file_safe(IDENTITY_FILE).replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT)))

    # 2. Discipline nudges — the agent must see them before it starts working.
    if not restore:
        for hint in (
            maybe_caps_prompt(content),
            maybe_session_block_hint(content),
            maybe_stale_refs_hint(),
            maybe_rails_hint(),
        ):
            add_raw(hint)

    # 3. Stats. The session counter counts sessions, not hook runs.
    if not restore:
        counter = bump_session_counter if writer else peek_session_counter
        add_raw(build_stats(counter(session_key) if full else None, content))

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


def units(text: str) -> int:
    """Length as Claude Code counts it (a JS string: UTF-16 code units), not Python code points."""
    return len(text.encode("utf-16-le")) // 2


def split_lines(text: str) -> list[str]:
    """Lines with their `\n` kept — only `\n` splits (str.splitlines also splits on \r, \x0c, …)."""
    lines = text.split("\n")
    out = [line + "\n" for line in lines[:-1]]
    if lines[-1]:
        out.append(lines[-1])
    return out


def cut_line(line: str, limit: int) -> list[str]:
    """A single line over the limit: pieces that each end in LINE_CUT_MARK except the last."""
    room = limit - units(LINE_CUT_MARK)
    pieces: list[str] = []
    start = used = 0
    for i, ch in enumerate(line):
        width = 2 if ord(ch) > 0xFFFF else 1
        if used + width > room:
            pieces.append(line[start:i] + LINE_CUT_MARK)
            start, used = i, 0
        used += width
    pieces.append(line[start:])
    return pieces


def split_parts(text: str, limit: int = PART_LIMIT) -> list[str]:
    """Pack the text into parts of <= limit at section boundaries (`# ` / `## ` lines).

    A section over the limit breaks at line boundaries; a single line over it is cut with
    LINE_CUT_MARK. Joined, the parts are the text (once the marks are removed).
    """
    bounds = [0, *(m.end() for m in SECTION_START_RE.finditer(text)), len(text)]
    atoms: list[str] = []
    for a, b in zip(bounds, bounds[1:]):
        section = text[a:b]
        if units(section) <= limit:
            atoms.append(section)
            continue
        for line in split_lines(section):
            atoms.extend([line] if units(line) <= limit else cut_line(line, limit))
    parts: list[str] = []
    current, size = "", 0
    for atom in atoms:
        width = units(atom)
        if current and size + width > limit:
            parts.append(current)
            current, size = "", 0
        current += atom
        size += width
    if current:
        parts.append(current)
    return parts


def render_part(parts: list[str], n: int) -> str:
    """Part n (1-based) with its wrapper line; "" past the last part or past MAX_PARTS."""
    if n < 1 or n > len(parts) or n > MAX_PARTS:
        return ""
    body = parts[n - 1]
    if n == MAX_PARTS and len(parts) > MAX_PARTS:
        body = body.rstrip("\n") + "\n" + OVERFLOW_LINE + "\n"
    return PART_HEADER.format(n=n, k=len(parts)) + body


def part_arg(argv: list[str]) -> int | None:
    """`--part N` / `--part=N`; None when absent. A malformed value is part 0 (prints nothing)."""
    for i, arg in enumerate(argv):
        value = None
        if arg == "--part":
            value = argv[i + 1] if i + 1 < len(argv) else ""
        elif arg.startswith("--part="):
            value = arg.split("=", 1)[1]
        if value is not None:
            try:
                return int(value)
            except ValueError:
                return 0
    return None


def main() -> None:
    part = part_arg(sys.argv[1:])
    payload = read_hook_input()
    source = str(payload.get("source") or "startup")
    session_id = payload.get("session_id")
    session_key = f"{session_id}|{source}" if isinstance(session_id, str) and session_id else None
    if part is None:
        text = build_context(source, True, session_key)
    else:
        if not 1 <= part <= MAX_PARTS:
            return
        # Only part 1 writes: the parts run in parallel, and parts 2..N must see what part 1 saw.
        text = render_part(split_parts(build_context(source, part == 1, session_key)), part)
        if not text:
            return
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": text,
        }
    }
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
