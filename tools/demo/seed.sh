#!/usr/bin/env bash
# Build (or reset) the demo folder the README recording is made in.
#
#   tools/demo/seed.sh [~/dev/mk-demo]      # idempotent: wipes and re-seeds the folder
#
# The folder carries a hot cache with the em-dash pattern on three dates, one handoff, one
# project, the demo CLAUDE.md (English, terse, the PROPOSAL:/Session closed. markers the tape
# waits on) and acceptEdits permissions. Claude Code still asks once per session before the first
# write to .claude/memory (a "sensitive file", even in auto mode) — the tape answers that off camera.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
D="${1:-$HOME/dev/mk-demo}"

rm -rf "$D"
mkdir -p "$D/.claude/memory" "$D/.claude/rules" "$D/context/handoffs" "$D/knowledge/concepts" "$D/projects/nestle" "$D/projects/ikea"
cp "$HERE/MEMORY.seed.md"      "$D/.claude/memory/MEMORY.md"
cp "$HERE/handoff.seed.md"     "$D/context/handoffs/nestle-landing-2026-09-01.md"
cp "$HERE/../../plugins/memory-kit/templates/HANDOFF-TEMPLATE.md" "$D/context/handoffs/"
cp "$HERE/CLAUDE.demo.md"      "$D/CLAUDE.md"
cp "$HERE/settings.demo.json"  "$D/.claude/settings.local.json"
printf '# Knowledge index\n\n| Article | One line |\n|---|---|\n| (none yet) | promoted patterns land here after your yes |\n' > "$D/knowledge/index.md"
printf '# Nestlé — landing page\n\n| Document class | Where |\n|---|---|\n| Backlog | projects/nestle/BACKLOG.md |\n| Plans | projects/nestle/plans/ |\n| Materials | projects/nestle/materials/ |\n' > "$D/projects/nestle/README.md"
printf '# Backlog — Nestlé\n\n- [ ] pricing tiers in the client voice\n- [ ] FAQ draft\n- [x] hero copy (approved 2026-09-01)\n' > "$D/projects/nestle/BACKLOG.md"
mkdir -p "$D/projects/ikea"
printf '# IKEA — Q4 catalog\n\n| Document class | Where |\n|---|---|\n| Backlog | projects/ikea/BACKLOG.md |\n| Materials | projects/ikea/materials/ |\n\nContact: Anna (marketing lead). Weekly status every Friday, three bullets.\n' > "$D/projects/ikea/README.md"
printf '# Backlog — IKEA\n\n- [ ] Q4 catalog brief — first draft due Thursday 2026-09-04\n- [ ] weekly status for Anna (Friday)\n- [x] kickoff notes filed (2026-08-27)\n' > "$D/projects/ikea/BACKLOG.md"
printf '.claude/state/\n' > "$D/.gitignore"
( cd "$D" && git init -q . && git add -A && git commit -qm "seed demo" )

# Claude Code's folder-trust dialog cannot be answered from the tape reliably — pre-accept it.
python3 - "$D" <<'PY'
import json, os, sys
p = os.path.expanduser("~/.claude.json"); d = json.load(open(p))
e = d.setdefault("projects", {}).setdefault(sys.argv[1], {})
e["hasTrustDialogAccepted"] = True; e.setdefault("hasCompletedProjectOnboarding", True)
json.dump(d, open(p, "w"), indent=2)
PY
echo "seeded $D"
