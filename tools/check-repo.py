#!/usr/bin/env python3
"""Repo integrity checks — the drift this kit keeps finding in other people's repos.

Deterministic, stdlib-only, no auth: runs in CI and on your machine identically.

  1. manifests parse, and VERSION / plugin.json / marketplace.json agree
  2. every marketplace `source` exists and holds a plugin manifest
  3. every hook command referenced in hooks.json exists and is executable; a hook with
     `onFailure: block` first proves its interpreter RUNS
     (`X -c 'import sys; sys.exit(sys.version_info < (3,9))' >/dev/null 2>&1 || exit 0; X ...`), and no hook
     uses the `command -v` form (it passes the macOS python3 stub, which exists and exits 1)
  4. every skill has frontmatter with a description; every agent has a name
  5. every relative link and every image embed in the markdown resolves
  6. no asset in .github/assets is orphaned (nothing embeds or links it)
  7. the hot-path budget: every SKILL.md and every agent body under its byte ceiling
     (warning at 90 % of it, failure over 100 %)

usage: python3 tools/check-repo.py     # exit 1 on any failure
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fail: list[str] = []
warn: list[str] = []

# Check 7 — the hot-path budget. A skill body and an agent body are loaded whole the moment they
# are invoked, so their size is a context bill, not a file size. Ceilings from
# docs/plans/2026-09-17-v7-dev-lifecycle.md § Value sources.
BUDGETS = (
    ("plugins/*/skills/*/SKILL.md", 24_000),
    ("plugins/*/agents/*.md", 8_000),
)
WARN_AT = 0.9  # a file at 90 % of its ceiling is the last moment to split it, not the first


def check(cond: bool, msg: str) -> None:
    if not cond:
        fail.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — any parse problem is a failure
        fail.append(f"{path}: {exc}")
        return None


# 1 + 2 — manifests -----------------------------------------------------------------
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
market = load(ROOT / ".claude-plugin" / "marketplace.json") or {}
for entry in market.get("plugins", []):
    src = ROOT / entry["source"]
    manifest = src / ".claude-plugin" / "plugin.json"
    check(manifest.exists(), f"marketplace entry {entry['name']}: no manifest at {manifest}")
    if manifest.exists():
        plugin = load(manifest) or {}
        check(plugin.get("version") == version,
              f"{manifest}: version {plugin.get('version')} != VERSION {version}")
        check(entry.get("version") == version,
              f"marketplace entry {entry['name']}: version {entry.get('version')} != VERSION {version}")

# 3 — hooks -------------------------------------------------------------------------
RUNS_CHECK_RE = re.compile(
    r"(\S+) -c " + re.escape("'import sys; sys.exit(sys.version_info < (3,9))' >/dev/null 2>&1 || exit 0; ")
    + r"(\S+) "
)
for hooks_json in ROOT.glob("plugins/*/hooks/hooks.json"):
    plugin_root = hooks_json.parent.parent
    cfg = load(hooks_json) or {}
    for event, groups in cfg.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                tokens = re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}[^"\s]*', cmd)
                shown = ", ".join(Path(t).name for t in tokens) or cmd[:80]
                for token in tokens:
                    target = plugin_root / token.replace("${CLAUDE_PLUGIN_ROOT}/", "")
                    check(target.exists(), f"{hooks_json} [{event}]: missing {target}")
                    check(target.exists() and os.access(target, os.X_OK),
                          f"{hooks_json} [{event}]: {target.name} is not executable")
                # 7.3: a hook whose failure BLOCKS the action must not fail because its interpreter cannot run —
                # that would block every matching tool call. Its command first proves the interpreter RUNS: the
                # macOS /usr/bin/python3 is a stub that exists and exits 1, so `command -v` is not enough (7.3 r2).
                if hook.get("onFailure") == "block":
                    m = RUNS_CHECK_RE.match(cmd)
                    check(bool(m) and m.group(1) == m.group(2),
                          f"{hooks_json} [{event}]: onFailure block without the interpreter-runs check: {shown}")
                check("command -v" not in cmd,
                      f"{hooks_json} [{event}]: `command -v` passes an interpreter stub that cannot run — use the "
                      f"interpreter-runs check: {shown}")

# 4 — skills and agents -------------------------------------------------------------
for skill in ROOT.glob("plugins/*/skills/*/SKILL.md"):
    head = skill.read_text(encoding="utf-8")[:1200]
    check(head.startswith("---"), f"{skill}: no frontmatter")
    check("description:" in head, f"{skill}: frontmatter has no description")
for agent in ROOT.glob("plugins/*/agents/*.md"):
    head = agent.read_text(encoding="utf-8")[:400]
    check(head.startswith("---") and "name:" in head, f"{agent}: no name in frontmatter")

# 5 + 6 — links and assets ----------------------------------------------------------
link_re = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
embedded: set[Path] = set()
for md in ROOT.rglob("*.md"):
    if ".git/" in str(md) or "node_modules" in str(md):
        continue
    for target in link_re.findall(md.read_text(encoding="utf-8", errors="ignore")):
        target = target.split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (md.parent / target).resolve()
        check(resolved.exists(), f"{md.relative_to(ROOT)}: dead link -> {target}")
        if resolved.suffix.lower() in {".png", ".jpg", ".svg", ".gif", ".mp4", ".webm"}:
            embedded.add(resolved)   # an embed or a plain link — both keep an asset alive

for asset in (ROOT / ".github" / "assets").glob("*"):
    if asset.name == "og-banner.png":
        continue  # also used as the social preview, embedded or not
    check(asset.resolve() in embedded, f"orphan asset: {asset.relative_to(ROOT)} is embedded nowhere")

# 7 — hot-path budget ---------------------------------------------------------------
for pattern, ceiling in BUDGETS:
    for path in sorted(ROOT.glob(pattern)):
        size = path.stat().st_size
        rel = path.relative_to(ROOT)
        check(size <= ceiling,
              f"hot-path budget: {rel} is {size} B, over the {ceiling} B ceiling")
        if ceiling * WARN_AT <= size <= ceiling:
            warn.append(f"{rel} is {size} B — {size * 100 // ceiling} % of its {ceiling} B ceiling")

# 8 — the README shows the whole plugin ---------------------------------------------
# A plugin install hides its file tree, so the root README is the only place a newcomer sees what
# ships. Every shipped part must be named there; the plugin README (the directory listing) must name
# every skill, agent and hook. A part added without its README line fails here, not in a reader's trust.
def shipped_parts(plugin: Path) -> dict[str, list[str]]:
    hooks = [p.name for p in sorted((plugin / "hooks").glob("*")) if p.suffix in (".py", ".sh")]
    hooks += [p.name for p in sorted((plugin / "hooks" / "lib").glob("*")) if p.suffix in (".py", ".sh")]
    return {
        "skill": [p.parent.name for p in sorted(plugin.glob("skills/*/SKILL.md"))],
        "agent": [p.stem for p in sorted(plugin.glob("agents/*.md"))],
        "hook": hooks,
        "reference": [p.name for p in sorted((plugin / "reference").glob("*"))],
        "template": [p.name for p in sorted(plugin.glob("templates/**/*")) if p.is_file()]
        + [p.name for p in sorted(plugin.glob("skills/*/templates/*")) if p.is_file()],
        "script": [p.name for p in sorted((plugin / "scripts").glob("*")) if p.is_file()]
        + [p.name for p in sorted(plugin.glob("skills/*/scripts/*")) if p.is_file() and p.suffix in (".py", ".sh")
           and not p.name.endswith("_config.py")],
        "context": [p.name for p in sorted((plugin / "context").glob("*.md"))],
    }


root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
for plugin in sorted(ROOT.glob("plugins/*/")):
    if not (plugin / ".claude-plugin" / "plugin.json").exists():
        continue
    parts = shipped_parts(plugin)
    plugin_readme = (plugin / "README.md").read_text(encoding="utf-8") if (plugin / "README.md").exists() else ""
    for kind, names in parts.items():
        for name in names:
            check(name in root_readme, f"README inventory: the {kind} `{name}` ships but README.md never names it")
            if kind in ("skill", "agent") or (kind == "hook" and not name.startswith("_")
                                               and (plugin / "hooks" / name).exists()):
                check(f"`{name}`" in plugin_readme,
                      f"plugin README inventory: the {kind} `{name}` ships but {plugin.name}/README.md never names it")

# ----------------------------------------------------------------------------------
for w in warn:
    print("⚠ ", w)
if fail:
    print(f"✗ {len(fail)} problem(s):")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("✔ repo checks passed")
