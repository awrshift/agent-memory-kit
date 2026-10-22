#!/bin/bash
# PreCompact hook — makes sure memory is saved around a compaction, without ever breaking one.
#
# Memory counts as saved when MEMORY.md was written < 2 min ago AND sits inside all three caps
# (180 lines / 32 KB / 3000 chars per line). When it is not:
#   trigger "manual" (/compact)  → {"decision": "block", "reason": …}: the agent saves, the user
#                                  runs /compact again.
#   trigger "auto" (or missing)  → ALLOW, and write .claude/state/compact-unsaved (one line:
#                                  "<date> <time>	<reason>"). Blocking an auto compaction either skips
#                                  it (proactive) or FAILS the current request (recovery from a
#                                  context-limit error) — code.claude.com/docs/en/hooks §PreCompact,
#                                  read 2026-10-22. session-start.py, on source "compact", then puts a
#                                  loud "save MEMORY.md now" line at the head of the memory section and
#                                  clears the marker (7.3).
# Saved memory → allow, and an old marker is removed (it would describe a compaction that is over).
#
# v6: paths are the PROJECT's (a plugin can be installed user-wide, so $CLAUDE_PROJECT_DIR is
# the only correct root), an unadopted repository is never blocked, and the reason names the
# namespaced skill.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="$PROJECT_DIR/.claude/state"
MEMORY_FILE="$PROJECT_DIR/.claude/memory/MEMORY.md"

INPUT=$(cat)

# Not a Memory Kit repository → nothing to save, never stand in the way.
if [ ! -f "$MEMORY_FILE" ] && [ ! -d "$PROJECT_DIR/context/handoffs" ]; then
    echo '{}'
    exit 0
fi

mkdir -p "$STATE_DIR"
MARKER="$STATE_DIR/compact-unsaved"
# One parse: "<session_id> <trigger>"; anything unreadable is "unknown auto" (never block blind).
read -r SESSION_ID TRIGGER <<< "$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    d = d if isinstance(d, dict) else {}
except Exception:
    d = {}
sid = "".join(c for c in str(d.get("session_id") or "") if c.isalnum() or c in "_-") or "unknown"
print(sid, "manual" if d.get("trigger") == "manual" else "auto")
' 2>/dev/null)"
SESSION_ID=$(printf '%s' "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"
[ "$TRIGGER" = "manual" ] || TRIGGER="auto"
echo "[$(date '+%H:%M:%S')] PRE-COMPACT ($TRIGGER) triggered for session $SESSION_ID" >> "$STATE_DIR/hook.log"

MEMORY_LINES=0
MEMORY_BYTES=0
MEMORY_MAX_LINE=0
MEMORY_AGE="unknown"
FRESH=0
if [ -f "$MEMORY_FILE" ]; then
    MEMORY_LINES=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
    MEMORY_BYTES=$(wc -c < "$MEMORY_FILE" | tr -d ' ')
    MEMORY_MAX_LINE=$(awk '{ if (length($0) > m) m = length($0) } END { print m + 0 }' "$MEMORY_FILE")
    # Not `stat`: `-f '%m'` is "format" on BSD/macOS but "file system" on GNU/Linux, where it
    # succeeds with junk output, the `||` fallback never runs, and the age arithmetic breaks —
    # which blocked EVERY compaction on Linux. python3 is already required by the hook.
    MEMORY_MTIME=$(python3 -c 'import os,sys; print(int(os.stat(sys.argv[1]).st_mtime))' "$MEMORY_FILE" 2>/dev/null)
    if [ -n "$MEMORY_MTIME" ]; then
        AGE_SECONDS=$(( $(date +%s) - MEMORY_MTIME ))
        [ "$AGE_SECONDS" -lt 120 ] && FRESH=1
        MEMORY_AGE="$((AGE_SECONDS / 60)) min ago"
    fi
fi

# Which caps are tripped — the reason must name the real problem, not call a fresh file stale.
OVER=""
[ "$MEMORY_LINES" -gt 180 ] && OVER="${OVER}lines ${MEMORY_LINES}/180; "
[ "$MEMORY_BYTES" -gt 32768 ] && OVER="${OVER}size $((MEMORY_BYTES / 1024)) KB/32 KB; "
[ "$MEMORY_MAX_LINE" -gt 3000 ] && OVER="${OVER}longest line ${MEMORY_MAX_LINE}/3000 chars; "

if [ "$FRESH" -eq 1 ] && [ -z "$OVER" ]; then
    echo "[$(date '+%H:%M:%S')] MEMORY.md fresh (${AGE_SECONDS}s, ${MEMORY_LINES} lines) — allowing compact" >> "$STATE_DIR/hook.log"
    rm -f "$MARKER"
    echo '{}'
    exit 0
fi

if [ -n "$OVER" ]; then
    # Fresh or not, an oversized cache must be pruned, not merely refreshed.
    PROBLEM="your hot cache is OVER its caps (${OVER%; }) — last updated ${MEMORY_AGE}"
    STEP1=".claude/memory/MEMORY.md — PRUNE it back inside the caps (180 lines / 32 KB / 3000 chars per line): promote settled 3+-date patterns to knowledge/concepts/, drop what a handoff already holds, then REPLACE the header current-state lines and add this session's date-tagged patterns"
else
    PROBLEM="your memory files are stale (MEMORY.md: ${MEMORY_LINES}/180 lines, last updated ${MEMORY_AGE})"
    STEP1=".claude/memory/MEMORY.md — REPLACE the header current-state lines and add this session's date-tagged patterns (caps: 180 lines / 32 KB / 3000 chars per line)"
fi

if [ "$TRIGGER" != "manual" ]; then
    # Never block an auto compaction (see the header): leave the marker for the SessionStart that follows.
    printf '%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PROBLEM" > "$MARKER"
    echo "[$(date '+%H:%M:%S')] ALLOWING auto compact over unsaved memory — ${PROBLEM}; marker written" >> "$STATE_DIR/hook.log"
    echo '{}'
    exit 0
fi

echo "[$(date '+%H:%M:%S')] BLOCKING compact — ${PROBLEM}" >> "$STATE_DIR/hook.log"

cat << HOOKJSON
{
  "decision": "block",
  "reason": "CONTEXT COMPRESSION IMMINENT and ${PROBLEM}. Save before compaction proceeds:\n\n1. ${STEP1}\n2. context/handoffs/ — write or refresh this session's handoff: what was done + the immediate next step\n\nWrite these files NOW, then continue. Full ritual: /memory-kit:close-session."
}
HOOKJSON
