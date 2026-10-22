# The one way a Memory Kit shell hook writes to <project>/.claude/state/ (7.3) — sourced, not run.
#
# Twin of statefs.py, same rule: a write is refused (silently — the hook never fails over bookkeeping) when
# .claude or .claude/state is a symlink, when .claude/state resolves outside the project, or when the target
# entry is a symlink. A cloned repo could otherwise point any of them at ~/.bashrc. A replacement is written
# to a fresh `mktemp` file in the state directory and moved over the entry (never a fixed temp name).
# Callers set PROJECT_DIR and STATE_DIR (= "$PROJECT_DIR/.claude/state") and check adoption themselves.
# Tests: hooks/tests/test_state_symlinks.py.

# 0 when $STATE_DIR is safe to write in (made when missing) and entry $1 (optional) is not a symlink.
cmk_state_ok() {
    [ -L "$PROJECT_DIR/.claude" ] && return 1
    [ -L "$STATE_DIR" ] && return 1
    if [ ! -d "$STATE_DIR" ]; then
        [ -e "$STATE_DIR" ] && return 1
        mkdir -p "$STATE_DIR" 2>/dev/null || return 1
        [ -L "$PROJECT_DIR/.claude" ] || [ -L "$STATE_DIR" ] && return 1
    fi
    local real root
    real=$(cd "$STATE_DIR" 2>/dev/null && pwd -P) || return 1
    root=$(cd "$PROJECT_DIR" 2>/dev/null && pwd -P) || return 1
    case "$real" in
        "$root"/*) ;;
        *) return 1 ;;
    esac
    [ -n "${1:-}" ] && [ -L "$1" ] && return 1
    return 0
}

# cmk_state_append FILE LINE — one line appended to a state file.
cmk_state_append() {
    cmk_state_ok "$1" || return 0
    printf '%s\n' "$2" >> "$1" 2>/dev/null || true
}

# cmk_state_replace FILE LINE — the file replaced whole by one line.
cmk_state_replace() {
    cmk_state_ok "$1" || return 0
    local tmp
    tmp=$(mktemp "$STATE_DIR/.cmk.XXXXXX" 2>/dev/null) || return 0
    if printf '%s\n' "$2" > "$tmp" 2>/dev/null && ! [ -L "$1" ]; then
        mv -f "$tmp" "$1" 2>/dev/null || rm -f "$tmp"
    else
        rm -f "$tmp"
    fi
    return 0
}

# cmk_state_remove FILE — removed only when it is a plain entry of a safe state directory.
cmk_state_remove() {
    cmk_state_ok "$1" || return 0
    rm -f "$1" 2>/dev/null || true
}
