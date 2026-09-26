"""Permission-rails facts, shared by the SessionStart nudge and the system-audit gates script.

Read-only, stdlib only, no subprocess, Python 3.9+. Every function swallows its own I/O errors —
a malformed settings file must never break a hook.

- `load_permissions(project_dir)` — `permissions.{allow,deny,ask}` merged from
  `~/.claude/settings.json`, `<project>/.claude/settings.json`, `<project>/.claude/settings.local.json`.
- `env_files(project_dir)` — root-level secret files that exist (`.env`, `.env.local`,
  `.env.*.local`, `.env.development|production|test`, `*.pem`); never `.env.example` / `.env.sample`.
- `uncovered_env_files(project_dir, perms)` — those with no `Read` deny rule covering them.
- `broad_allows(perms)` — allow rules that hand a whole tool to the agent (`Bash(*)`, `Bash(git *)`, …)
  or let an interpreter run any file of a folder (`Bash(node scripts/*)`).
- `rails_line(project_dir)` — the one-line SessionStart nudge, or "".

The path matching approximates Claude Code's gitignore-style rules (`//abs`, `~/home`, `/root-rel`,
`./rel`, `**`, `*`) closely enough for a nudge; it is not the permission engine.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ENV_NAME_RE = re.compile(r"^\.env(?:\.local|\.development|\.production|\.test|\.[^/]+\.local)?$|\.pem$")
ENV_EXAMPLES = {".env.example", ".env.sample"}
BROAD_TOOLS = "git|gh|docker|curl|node|python3?|npx|pnpm|bash|sh"
BROAD_ALLOW_RE = re.compile(r"^Bash(?:\((?:\*|(?:%s)(?: \*|:\*| ?\*))\))?$" % BROAD_TOOLS)
# An interpreter over a path wildcard (`Bash(node scripts/*)`, `Bash(python3 tools/*.py)`) is broad too:
# the agent can write a new file into that folder and run it before the classifier sees it.
INTERPRETERS = "node|python3?|bash|sh|zsh|deno|bun|ruby|perl|tsx|ts-node"
PATH_WILDCARD_ALLOW_RE = re.compile(r"^Bash\((?:%s) +[^\s:*]*/[^\s:]*\*" % INTERPRETERS)  # the * must sit INSIDE the path; `scripts/x.py:*` / `scripts/x.py *` are exact-script allows
STATE_MARKERS = ("rails-v2", "rails-declined")


def _settings_paths(project_dir: Path):
    return (
        Path.home() / ".claude" / "settings.json",
        project_dir / ".claude" / "settings.json",
        project_dir / ".claude" / "settings.local.json",
    )


def load_settings(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load_permissions(project_dir: Path) -> dict:
    merged = {"allow": [], "deny": [], "ask": []}
    for path in _settings_paths(project_dir):
        perms = load_settings(path).get("permissions")
        if not isinstance(perms, dict):
            continue
        for key in merged:
            rules = perms.get(key)
            if isinstance(rules, list):
                merged[key] += [r for r in rules if isinstance(r, str)]
    return merged


def env_files(project_dir: Path) -> list:
    try:
        names = sorted(os.listdir(project_dir))
    except OSError:
        return []
    return [
        n for n in names
        if n not in ENV_EXAMPLES and ENV_NAME_RE.search(n) and (project_dir / n).is_file()
    ]


def _glob_re(pattern: str):
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def _covers(rule: str, project_dir: Path, name: str) -> bool:
    m = re.match(r"^Read(?:\((.*)\))?$", rule.strip())
    if not m:
        return False
    spec = (m.group(1) or "").strip()
    if spec in ("", "*", "**", "./**", "/**"):
        return True
    target = str(project_dir / name)
    if spec.startswith("//"):
        return bool(_glob_re(spec[1:]).match(target))
    if spec.startswith("~/"):
        return bool(_glob_re(os.path.expanduser(spec)).match(target))
    rel = spec[2:] if spec.startswith("./") else spec.lstrip("/")
    if "/" not in rel.rstrip("/"):  # a bare name matches at any depth, root included
        rel = "**/" + rel
    return bool(_glob_re(rel).match(name))


def uncovered_env_files(project_dir: Path, perms: dict) -> list:
    return [
        n for n in env_files(project_dir)
        if not any(_covers(rule, project_dir, n) for rule in perms.get("deny", []))
    ]


def broad_allows(perms: dict) -> list:
    return [
        r for r in perms.get("allow", [])
        if BROAD_ALLOW_RE.match(r.strip()) or PATH_WILDCARD_ALLOW_RE.match(r.strip())
    ]


def _short(items, limit=3):
    shown = ", ".join("`%s`" % i for i in items[:limit])
    return shown + (" +%d more" % (len(items) - limit) if len(items) > limit else "")


def rails_line(project_dir: Path) -> str:
    """The one SessionStart line, or "" — silent once rails are installed or declined."""
    try:
        state = project_dir / ".claude" / "state"
        if any((state / marker).exists() for marker in STATE_MARKERS):
            return ""
        perms = load_permissions(project_dir)
        what = []
        uncovered = uncovered_env_files(project_dir, perms)
        if uncovered:
            what.append("%s readable (no Read deny)" % _short(uncovered))
        broad = broad_allows(perms)
        if broad:
            what.append("broad allow %s" % _short(broad))
        if not what:
            return ""
        return (
            "Rails: %s — run `/memory-kit:setup rails` (or it is declined: touch "
            ".claude/state/rails-declined)." % "; ".join(what)
        )
    except Exception:  # noqa: BLE001 — a nudge must never break the hook
        return ""
