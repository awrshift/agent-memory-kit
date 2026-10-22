# AC-7 measurement: run hooks/lib/legacy_hooks.find_copies over every <root>/*/ with .claude/memory/MEMORY.md
# (read-only: the function only reads settings files and wired scripts). Compares with the expected sets.
import os, sys
from pathlib import Path
sys.dont_write_bytecode = True
plugin, root = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, os.path.join(plugin, "hooks", "lib"))
import legacy_hooks
EXPECT_FLAGGED = {"project-09", "project-08", "project-05", "project-03", "project-06",
                  "project-04", "project-10", "project-12"}
EXPECT_CLEAN = {"project-01", "project-07"}
repos = sorted(p for p in root.iterdir() if (p / ".claude/memory/MEMORY.md").is_file())
flagged, clean = [], []
for repo in repos:
    copies = legacy_hooks.find_copies(repo)
    wired = sum(1 for rel in legacy_hooks.SETTINGS for ev, gs in (legacy_hooks._load(repo / rel).get("hooks") or {}).items()
                if isinstance(gs, list) for g in gs if isinstance(g, dict) for h in (g.get("hooks") or []))
    tag = "disabled" if legacy_hooks.plugin_disabled(repo) else ""
    print("%-28s wired=%-2d flagged=%-2d %s %s" % (repo.name, wired, len(copies), tag,
          "; ".join("%s:%s" % (e, s.split('/')[-1]) for _, e, s, _ in copies)))
    (flagged if copies else clean).append(repo.name)
print("\nrepos scanned:", len(repos), "| flagged:", len(flagged), "| not flagged:", len(clean))
print("expected flagged but missed (missed duplicates):", sorted(EXPECT_FLAGGED - set(flagged)))
print("expected clean but flagged (legit flagged):", sorted(EXPECT_CLEAN & set(flagged)))
print("flagged outside the expected list:", sorted(set(flagged) - EXPECT_FLAGGED))
