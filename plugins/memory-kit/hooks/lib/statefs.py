"""The one way a Memory Kit Python hook touches `<project>/.claude/state/` (7.3).

A cloned repository can ship `.claude`, `.claude/state` or a file in it as a symlink — to ~/.bashrc, say —
and a hook that appends a log line or replaces a counter there would write the target. So every write,
removal and read of a state file goes through here, and is refused (silently: the caller carries on, a
hook never fails over bookkeeping) when:
  - `.claude` or `.claude/state` is a symlink, or `.claude/state` resolves outside the project;
  - the entry itself is a symlink (`lstat`).
Adoption is the caller's check (session-start, pre-compact, session-end write only in an adopted repo;
protect-tests keeps its ledger in any repo, as before 7.3).
A replacement is a fresh `tempfile.mkstemp` file in the state directory renamed over the entry, never a fixed
temp name; an append opens with O_NOFOLLOW. A read of a symlinked entry returns None, so a planted link
neither feeds the hooks nor gets consumed.

The shell twin is `state.sh`; tests: `hooks/tests/test_state_symlinks.py`.
Python 3.9+, stdlib only.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def state_dir(project_dir: Path, create: bool = False) -> Path | None:
    """`<project>/.claude/state` when it is safe to use, else None. `create` makes it when missing."""
    claude = project_dir / ".claude"
    state = claude / "state"
    if claude.is_symlink() or state.is_symlink():
        return None
    if not state.is_dir():
        if not create or state.exists():
            return None
        try:
            state.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
        if claude.is_symlink() or state.is_symlink():
            return None
    try:
        real = state.resolve(strict=True)
        root = project_dir.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if root not in real.parents:
        return None
    return state


def entry(project_dir: Path, name: str, create: bool = False) -> Path | None:
    """The path of state file `name` when it may be written or read (not a symlink, in a safe directory)."""
    if not name or "/" in name or name in (".", ".."):
        return None
    base = state_dir(project_dir, create)
    if base is None:
        return None
    path = base / name
    return None if path.is_symlink() else path


def read_text(project_dir: Path, name: str) -> str | None:
    path = entry(project_dir, name)
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def write_atomic(project_dir: Path, name: str, text: str) -> bool:
    """Replace state file `name` whole; a parallel reader sees the old file or the new one, never a torn write."""
    path = entry(project_dir, name, create=True)
    if path is None:
        return False
    try:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".cmk-", suffix=".tmp")
    except OSError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        if path.is_symlink():  # re-checked just before the rename
            raise OSError("symlink appeared")
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return False


def append_line(project_dir: Path, name: str, line: str) -> bool:
    path = entry(project_dir, name, create=True)
    if path is None:
        return False
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags, 0o644)
    except OSError:
        return False
    try:
        os.write(fd, (line.rstrip("\n") + "\n").encode("utf-8"))
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def remove(project_dir: Path, name: str) -> bool:
    path = entry(project_dir, name)
    if path is None:
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def mtime(project_dir: Path, name: str) -> float | None:
    path = entry(project_dir, name)
    if path is None:
        return None
    try:
        return path.stat().st_mtime
    except OSError:
        return None
