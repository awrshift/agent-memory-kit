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

TOOL_NAME=$(echo "$INPUT" | grep -oE '"tool_name"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')
FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

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
