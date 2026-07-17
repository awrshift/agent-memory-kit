#!/bin/bash
# PreCompact hook — BLOCKS compaction until agent saves context
#
# Uses exit 0 + JSON {"decision": "block"} for graceful blocking.
# Checks MEMORY.md mtime — if updated < 2 min ago, allows (agent already saved).
# Otherwise blocks with dynamic context (line count, staleness, project count).

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"
mkdir -p "$STATE_DIR"

MEMORY_FILE="$PROJECT_DIR/.claude/memory/MEMORY.md"

# Read JSON input from stdin
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null)
SESSION_ID=$(echo "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"

echo "[$(date '+%H:%M:%S')] PRE-COMPACT triggered for session $SESSION_ID" >> "$STATE_DIR/hook.log"

# Collect dynamic context
MEMORY_LINES=0
MEMORY_AGE="unknown"
if [ -f "$MEMORY_FILE" ]; then
    MEMORY_LINES=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
    MEMORY_BYTES=$(wc -c < "$MEMORY_FILE" | tr -d ' ')
    MEMORY_MAX_LINE=$(awk '{ if (length($0) > m) m = length($0) } END { print m + 0 }' "$MEMORY_FILE")
    MEMORY_MTIME=$(stat -f '%m' "$MEMORY_FILE" 2>/dev/null || stat -c '%Y' "$MEMORY_FILE" 2>/dev/null)
    NOW=$(date +%s)
    if [ -n "$MEMORY_MTIME" ]; then
        AGE_SECONDS=$((NOW - MEMORY_MTIME))
        # Fresh AND under all three caps (180 lines / 32 KB / 3000 chars-per-line)
        if [ "$AGE_SECONDS" -lt 120 ] && [ "$MEMORY_LINES" -le 180 ] \
           && [ "$MEMORY_BYTES" -le 32768 ] && [ "$MEMORY_MAX_LINE" -le 3000 ]; then
            echo "[$(date '+%H:%M:%S')] MEMORY.md fresh ($AGE_SECONDS sec ago, $MEMORY_LINES lines), allowing compact" >> "$STATE_DIR/hook.log"
            echo '{}'
            exit 0
        fi
        MEMORY_AGE="$((AGE_SECONDS / 60)) min ago"
    fi
fi

# Count active projects
PROJECT_COUNT=0
if [ -d "$PROJECT_DIR/projects" ]; then
    PROJECT_COUNT=$(find "$PROJECT_DIR/projects" -name "BACKLOG.md" -type f 2>/dev/null | wc -l | tr -d ' ')
fi

echo "[$(date '+%H:%M:%S')] BLOCKING compact — MEMORY.md last updated $MEMORY_AGE" >> "$STATE_DIR/hook.log"

cat << HOOKJSON
{
  "decision": "block",
  "reason": "CONTEXT COMPRESSION IMMINENT. Your memory files are stale (MEMORY.md: ${MEMORY_LINES}/180 lines, last updated ${MEMORY_AGE}). You MUST save before compaction proceeds:\n\n1. Update .claude/memory/MEMORY.md — REPLACE the header current-state lines + add new date-tagged patterns (caps: 180 lines / 32 KB / 3000 chars per line)\n2. Write/refresh this session's handoff in context/handoffs/ (copy HANDOFF-TEMPLATE.md) — what was done + immediate next\n3. Update project BACKLOG.md — task statuses (${PROJECT_COUNT} project(s) active)\n\nWrite to these files NOW. Compaction will proceed after files are updated."
}
HOOKJSON
