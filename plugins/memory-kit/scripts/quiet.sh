#!/usr/bin/env bash
# Run a long, noisy command (commit hooks, vitest, tsc, pre-pr-check) and keep the agent's context small:
# the FULL output goes to a log file; the screen gets the exit code, the summary lines and — only on failure —
# the failing blocks and the tail. Nothing is hidden on failure; on success only the summary is shown.
#
# Usage: bash .claude/scripts/quiet.sh <command> [args...]
#   e.g. bash .claude/scripts/quiet.sh git commit -m "…" -- <paths>
#        bash .claude/scripts/quiet.sh npx vitest run
set -uo pipefail

LOG_DIR="${QUIET_LOG_DIR:-${TMPDIR:-/tmp}/quiet-logs}"
mkdir -p "${LOG_DIR}"
LOG="${LOG_DIR}/$(date +%Y%m%d-%H%M%S)-$$.log"

"$@" >"${LOG}" 2>&1
code=$?

# Strip ANSI colours for the on-screen part (the log keeps the raw bytes).
plain() { LC_ALL=C sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' "${LOG}"; }

echo "exit=${code}  log=${LOG}  ($(LC_ALL=C wc -c <"${LOG}" | tr -d ' ') bytes)"
plain | grep -E 'Test Files|Tests +[0-9]|error TS|✔️|✗|🥊 .*hook:|RESULT:|^\[[^]]+ [0-9a-f]{7,}\]|problems? \(' | head -30

if [ "${code}" -ne 0 ]; then
  echo "--- failing blocks"
  plain | grep -nE -A12 '(FAIL |✗|Error:|error TS|AssertionError|BLOCKED|OVERLAP|COPY|RETURN TYPE)' | head -120
  echo "--- tail"
  plain | tail -20
fi
exit "${code}"
