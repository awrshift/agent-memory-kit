#!/usr/bin/env python3
"""Repo integrity checks — the drift this kit keeps finding in other people's repos.

Deterministic, stdlib-only, no auth: runs in CI and on your machine identically.

  1. manifests parse, and VERSION / plugin.json / marketplace.json agree
     (both catalog families: .claude-plugin/ and .cursor-plugin/)
  2. every marketplace `source` exists and holds a plugin manifest
  3. every hook command referenced in hooks.json exists and is executable
  4. every skill has frontmatter with a description; every agent has a name
  5. every relative link and every image embed in the markdown resolves
  6. no asset in .github/assets is orphaned (nothing embeds it)

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

# 1 + 2 for the Cursor catalog — same shape, its own manifest filename
cursor_market_path = ROOT / ".cursor-plugin" / "marketplace.json"
if cursor_market_path.exists():
    cursor_market = load(cursor_market_path) or {}
    for entry in cursor_market.get("plugins", []):
        src = ROOT / entry["source"]
        manifest = src / ".cursor-plugin" / "plugin.json"
        check(manifest.exists(), f"cursor marketplace entry {entry['name']}: no manifest at {manifest}")
        if manifest.exists():
            plugin = load(manifest) or {}
            check(plugin.get("version") == version,
                  f"{manifest}: version {plugin.get('version')} != VERSION {version}")
            check(entry.get("version") == version,
                  f"cursor marketplace entry {entry['name']}: version {entry.get('version')} != VERSION {version}")

# 3 — hooks -------------------------------------------------------------------------
for hooks_json in ROOT.glob("plugins/*/hooks/hooks.json"):
    plugin_root = hooks_json.parent.parent
    cfg = load(hooks_json) or {}
    for event, groups in cfg.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                for token in re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}[^"\s]*', cmd):
                    target = plugin_root / token.replace("${CLAUDE_PLUGIN_ROOT}/", "")
                    check(target.exists(), f"{hooks_json} [{event}]: missing {target}")
                    check(target.exists() and os.access(target, os.X_OK),
                          f"{hooks_json} [{event}]: {target.name} is not executable")

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
    if ".git/" in str(md):
        continue
    for target in link_re.findall(md.read_text(encoding="utf-8", errors="ignore")):
        target = target.split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (md.parent / target).resolve()
        check(resolved.exists(), f"{md.relative_to(ROOT)}: dead link -> {target}")
        if resolved.suffix.lower() in {".png", ".jpg", ".svg", ".gif"}:
            embedded.add(resolved)

for asset in (ROOT / ".github" / "assets").glob("*"):
    if asset.name == "og-banner.png":
        continue  # also used as the social preview, embedded or not
    check(asset.resolve() in embedded, f"orphan asset: {asset.relative_to(ROOT)} is embedded nowhere")

# ----------------------------------------------------------------------------------
if fail:
    print(f"✗ {len(fail)} problem(s):")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("✔ repo checks passed")
