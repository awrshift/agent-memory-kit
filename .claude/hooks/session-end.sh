#!/usr/bin/env bash
#
# SessionEnd hook — log session close timestamp to state/.
#
# No auto-flush. Session-close synthesis is done via the `/close-session` skill
# (user-invoked, agent-driven audit ritual). See ARCHITECTURE.md §"audit ritual".
#
# This hook only records that a session closed; it does not spawn any
# background process. Recursion guard kept for compatibility with any
# future sub-agent invocations.

set -euo pipefail

# Recursion guard
if [[ -n "${CLAUDE_INVOKED_BY:-}" ]]; then
    exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"
mkdir -p "$STATE_DIR"
LOG_FILE="$STATE_DIR/session-end.log"

# Read stdin JSON
HOOK_INPUT=$(cat)
SESSION_ID=$(echo "$HOOK_INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")

echo "$(date '+%Y-%m-%d %H:%M:%S') [hook] SessionEnd: session=$SESSION_ID" >> "$LOG_FILE"

exit 0
