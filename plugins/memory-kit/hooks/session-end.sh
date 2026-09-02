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

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="$PROJECT_DIR/.claude/state"
mkdir -p "$STATE_DIR"
LOG_FILE="$STATE_DIR/session-end.log"

# Read stdin JSON — but never block on it. Claude Code cancels SessionEnd hooks that are
# still running when the process exits, and a bare `cat` on a stdin nobody closes is exactly
# that: every exit printed "SessionEnd hook … failed: Hook cancelled" (found 2026-09-02 while
# recording the demo). One second is plenty for a JSON payload that is already written.
SESSION_ID=$(python3 -c '
import json, select, sys
ready, _, _ = select.select([sys.stdin], [], [], 1.0)
raw = sys.stdin.read() if ready else ""
try:
    print(json.loads(raw).get("session_id", "unknown") or "unknown")
except Exception:
    print("unknown")
' 2>/dev/null || echo "unknown")

echo "$(date '+%Y-%m-%d %H:%M:%S') [hook] SessionEnd: session=$SESSION_ID" >> "$LOG_FILE"

exit 0
