#!/usr/bin/env bash
# Run a long, noisy command (commit hooks, vitest, tsc, pre-pr-check) and keep the agent's context small:
# the FULL output goes to a log file; the screen gets the exit code, the summary lines and — only on failure —
# the failing blocks and the tail. Nothing is hidden on failure; on success only the summary is shown.
#
# Usage: bash .claude/scripts/quiet.sh <command> [args...]
#   e.g. bash .claude/scripts/quiet.sh git commit -m "…" -- <paths>
#        bash .claude/scripts/quiet.sh npx vitest run
#
# A `git commit` is PROVEN to have landed. A pre-commit hook that re-formats the staged files can leave NO commit
# while the summary looks clean (three commits silently missing in one day in a kit project, 2026-11-10). So for
# `git commit` the LAST line printed is always `landed: <hash> <subject>` or `COMMIT NOT LANDED …`, and a commit that
# did not move HEAD exits non-zero whatever git returned. Read that line — never only the tail of a longer pipeline.
# Not covered: `git -C <dir> commit` (HEAD is read in the current directory) and `--dry-run` (skipped on purpose).
set -uo pipefail

is_commit=""
if [ "${1:-}" = "git" ] && [ "${2:-}" = "commit" ]; then
  is_commit=1
  for arg in "$@"; do [ "${arg}" = "--dry-run" ] && is_commit=""; done
fi
[ -n "${is_commit}" ] && head_before="$(git rev-parse -q --verify HEAD 2>/dev/null || echo none)"

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

if [ -n "${is_commit}" ]; then
  head_after="$(git rev-parse -q --verify HEAD 2>/dev/null || echo none)"
  if [ "${head_after}" = "${head_before}" ]; then
    echo "COMMIT NOT LANDED (git exit=${code}, HEAD still ${head_before:0:9}) — nothing was committed; read ${LOG}"
    [ "${code}" -eq 0 ] && code=1
  else
    echo "landed: $(git log -1 --format='%h %s' | cut -c1-120)"
  fi
fi
exit "${code}"
