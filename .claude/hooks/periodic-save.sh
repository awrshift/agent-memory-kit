#!/bin/bash
# Periodic Save hook — auto-checkpoint every N exchanges
#
# Claude Code "Stop" hook. Counts human messages in transcript.
# Every SAVE_INTERVAL exchanges, blocks the agent to save progress.
# Anti-loop: stop_hook_active=true → pass through immediately.

SAVE_INTERVAL="${CLAUDE_SAVE_INTERVAL:-50}"

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"
mkdir -p "$STATE_DIR"

# Read JSON input from stdin
INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null)
SESSION_ID=$(echo "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"

STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stop_hook_active', False))" 2>/dev/null)
TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('transcript_path',''))" 2>/dev/null)
TRANSCRIPT_PATH="${TRANSCRIPT_PATH/#\~/$HOME}"

# Anti-loop: if already in save cycle, let agent stop
if [ "$STOP_HOOK_ACTIVE" = "True" ] || [ "$STOP_HOOK_ACTIVE" = "true" ]; then
    echo '{}'
    exit 0
fi

# Count human messages in JSONL transcript
EXCHANGE_COUNT=0
if [ -f "$TRANSCRIPT_PATH" ]; then
    EXCHANGE_COUNT=$(python3 - "$TRANSCRIPT_PATH" <<'PYEOF'
import json, sys
count = 0
with open(sys.argv[1]) as f:
    for line in f:
        try:
            entry = json.loads(line)
            msg = entry.get('message', {})
            if isinstance(msg, dict) and msg.get('role') == 'user':
                content = msg.get('content', '')
                if isinstance(content, str) and '<command-message>' in content:
                    continue
                count += 1
        except:
            pass
print(count)
PYEOF
2>/dev/null)
fi

# Track last save point
LAST_SAVE_FILE="$STATE_DIR/${SESSION_ID}_last_save"
LAST_SAVE=0
[ -f "$LAST_SAVE_FILE" ] && LAST_SAVE=$(cat "$LAST_SAVE_FILE")

SINCE_LAST=$((EXCHANGE_COUNT - LAST_SAVE))

echo "[$(date '+%H:%M:%S')] Session $SESSION_ID: $EXCHANGE_COUNT exchanges, $SINCE_LAST since last save" >> "$STATE_DIR/hook.log"

if [ "$SINCE_LAST" -ge "$SAVE_INTERVAL" ] && [ "$EXCHANGE_COUNT" -gt 0 ]; then
    echo "$EXCHANGE_COUNT" > "$LAST_SAVE_FILE"
    echo "[$(date '+%H:%M:%S')] TRIGGERING PERIODIC SAVE at exchange $EXCHANGE_COUNT" >> "$STATE_DIR/hook.log"

    MEMORY_LINES=0
    [ -f "$PROJECT_DIR/.claude/memory/MEMORY.md" ] && MEMORY_LINES=$(wc -l < "$PROJECT_DIR/.claude/memory/MEMORY.md" | tr -d ' ')

    cat << HOOKJSON
{
  "decision": "block",
  "reason": "PERIODIC SAVE checkpoint (${EXCHANGE_COUNT} exchanges). Before continuing, save your progress:\n\n1. .claude/memory/MEMORY.md — any new date-tagged patterns from this session (currently ${MEMORY_LINES}/180 lines; caps 180 / 32 KB / 3000-per-line)\n2. context/handoffs/ — write/refresh this session's handoff (what was done + immediate next)\n3. projects/*/BACKLOG.md — update task statuses if changed\n\nContinue your work after saving."
}
HOOKJSON
else
    echo '{}'
fi
