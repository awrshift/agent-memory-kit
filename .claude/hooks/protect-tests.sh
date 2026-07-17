#!/bin/bash
# Hook: Protect test files from modification
# Exit code 2 = blocking error (agent must fix implementation, not tests)
# Exit code 0 = allowed (proceed)
#
# Triggered on PreToolUse for Edit and Write tools.
# Covers common test conventions (test_*.py, *_test.py, /tests/, /__tests__/,
# *.test.*, *.spec.*). Harmless no-op for projects with no tests — exits 0.
#
# Write (new file creation) is allowed. Only Edit (modifying existing) is blocked.

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Notes and docs are not code tests — never block them, even under a tests/ dir
case "$FILE_PATH" in
  *.md|*.txt) exit 0 ;;
esac

# Allow creating new test files (Write tool only)
if [ "$TOOL_NAME" = "Write" ] && [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# Block modifications to existing test files
# Patterns:
# - test_*.py or *_test.py (Python convention, any folder)
# - /tests/ or /__tests__/ folders
# - .test.* or .spec.* suffix (JS/TS)
if echo "$FILE_PATH" | grep -qiE '(^|/)test_[^/]+\.py$|(^|/)[^/]+_test\.py$|/__tests__/|/tests?/|\.test\.|\.spec\.'; then
  echo "BLOCKED: Test files are protected. Fix the implementation, not the tests." >&2
  echo "File: $FILE_PATH" >&2
  exit 2
fi

exit 0
