#!/usr/bin/env bash
# system-audit :: deterministic fact collector
# Usage: bash collect.sh [repo_root]   (default: git root of cwd, else cwd)
# Output: markdown to stdout. Read-only: never writes into the audited repo.
set -uo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT" || { echo "cannot cd to $ROOT"; exit 1; }
TODAY="$(date +%Y-%m-%d)"

# Files worth auditing: skip vcs/build/vendor noise.
PRUNE='-name .git -o -name node_modules -o -name .venv -o -name venv -o -name dist -o -name build -o -name __pycache__ -o -name .pytest_cache -o -name .next -o -name target -o -name output -o -name .worktrees'
find_src() { find . \( $PRUNE \) -prune -o "$@" -print 2>/dev/null; }
find_in()  { find "$1" \( $PRUNE \) -prune -o "${@:2}" -print 2>/dev/null; }

echo "# System audit — collected facts ($TODAY)"
echo
echo "repo: \`$ROOT\`"
echo

# ─────────────────────────────────────────── 1. layer inventory
echo "## 1. Layer inventory (which layers exist here)"
echo
echo '| layer | path | count |'
echo '|---|---|---|'
inv() { # label, path, glob
  local label="$1" p="$2" g="${3:-*}" n
  if [ -e "$p" ]; then
    n=$(find_in "$p" -type f -name "$g" | wc -l | tr -d ' ')
    echo "| $label | \`$p\` | $n |"
  else
    echo "| $label | — | н/п |"
  fi
}
inv "instructions"   "CLAUDE.md"            '*'
inv "rules"          ".claude/rules"        '*.md'
inv "skills (local)" ".claude/skills"       'SKILL.md'
inv "agents"         ".claude/agents"       '*.md'
inv "hooks cfg"      ".claude/settings.json" '*'
inv "memory"         ".claude/memory"       '*.md'
inv "handoffs"       "context/handoffs"     '*.md'
inv "audits (prior)" "context/audits"       '*.md'
inv "knowledge"      "knowledge"            '*.md'
inv "docs"           "docs"                 '*.md'
inv "projects"       "projects"             '*.md'
inv "experiments"    "experiments"          '*'
inv "tools"          "tools"                '*'
inv "infra"          "infra"                '*'
inv "tests"          "tests"                '*'
echo
echo "Prior audits (newest last):"
ls -1 context/audits/*.md 2>/dev/null | tail -3 || echo "- none"
echo

# ─────────────────────────────────────────── 2. doc frontmatter coverage
echo "## 2. Frontmatter / lifecycle coverage"
echo
total=0; withfm=0; missing=""
while IFS= read -r f; do
  case "$f" in ./node_modules/*|./.git/*) continue;; esac
  total=$((total+1))
  if head -1 "$f" 2>/dev/null | grep -q '^---$'; then withfm=$((withfm+1)); else missing="$missing$f\n"; fi
done < <(find_src -type f -name '*.md')
echo "- markdown docs: **$total**, with frontmatter: **$withfm**"
if [ "$total" -gt 0 ] && [ "$withfm" -lt "$total" ]; then
  echo "- without frontmatter (first 15):"
  printf "$missing" | head -15 | sed 's/^/  - /'
fi
echo "- docs carrying \`last_verified\`/\`last-reviewed\`: $(grep -rl -E '^(last_verified|last-reviewed):' --include='*.md' . 2>/dev/null | grep -cv node_modules)"
echo

# ─────────────────────────────────────────── 3. memory caps
echo "## 3. Memory caps"
echo
MEM=".claude/memory/MEMORY.md"
if [ -f "$MEM" ]; then
  L=$(wc -l < "$MEM" | tr -d ' '); B=$(wc -c < "$MEM" | tr -d ' ')
  MAXL=$(awk '{ if (length($0) > m) m = length($0) } END { print m+0 }' "$MEM")
  UND=$(grep -c -E '^[-*[:space:]]*\[[0-9]{4}-[0-9]{2}-[0-9]{2}\]' "$MEM")
  echo "- lines: $L / 180 · bytes: $B / 32768 · longest line: $MAXL / 3000"
  echo "- date-tagged entries: $UND"
  echo "- distinct dates in memory: $(grep -o -E '\[[0-9]{4}-[0-9]{2}-[0-9]{2}\]' "$MEM" | sort -u | wc -l | tr -d ' ')"
else
  echo "- н/п (no $MEM)"
fi
echo

# ─────────────────────────────────────────── 4. broken path references
echo "## 4. Broken path references in docs"
echo
echo "(directory-qualified paths in backticks that resolve neither from repo root nor from the"
echo "citing file's dir; bare filenames and \`YYYY\`-style templates are excluded as ambiguous)"
find_src -type f -name '*.md' | while IFS= read -r f; do
  grep -o -E '`[A-Za-z0-9_./-]+/[A-Za-z0-9_.-]+\.(md|py|sh|js|ts|json|yml|yaml|toml|txt)`' "$f" 2>/dev/null \
  | tr -d '`' | grep -v -E 'YYYY|MM|DD|<|\*' | sort -u | while IFS= read -r p; do
      [ -e "$p" ] || [ -e "$(dirname "$f")/$p" ] || echo "- \`$f\` → \`$p\`"
    done
done | sort -u | head -25
echo

# ─────────────────────────────────────────── 5. git activity & cold files
echo "## 5. Git activity"
echo
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "- branch: $(git rev-parse --abbrev-ref HEAD) · commits total: $(git rev-list --count HEAD 2>/dev/null)"
  echo "- commits last 30d: $(git log --since='30 days ago' --oneline 2>/dev/null | wc -l | tr -d ' ')"
  echo "- uncommitted tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
  echo "- untracked files: $(git status --porcelain --untracked-files=all | grep -c '^??')"
  echo "- branches other than current: $(git branch --format='%(refname:short)' | grep -cv "^$(git rev-parse --abbrev-ref HEAD)$")"
  echo "- worktrees: $(git worktree list 2>/dev/null | wc -l | tr -d ' ')"
  echo
  echo "Coldest tracked files (last commit date, oldest 15):"
  git ls-files | while IFS= read -r f; do
    d=$(git log -1 --format=%ad --date=short -- "$f" 2>/dev/null); [ -n "$d" ] && echo "$d $f"
  done | sort | head -15 | sed 's/^/  - /'
else
  echo "- н/п (not a git repo)"
fi
echo

# ─────────────────────────────────────────── 6. secrets & sensitive
echo "## 6. Secrets & sensitive material"
echo
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "- .env tracked in git: $(git ls-files | grep -c -E '(^|/)\.env$') (must be 0)"
  echo "- key-shaped files tracked: $(git ls-files | grep -c -i -E '\.(pem|key|p12|pfx)$|credentials|service.account')"
fi
if command -v gitleaks >/dev/null 2>&1; then
  echo "- gitleaks (working tree):"
  gitleaks detect --no-git --no-banner --redact -s . 2>&1 | tail -5 | sed 's/^/    /'
else
  echo "- gitleaks not installed — grep fallback:"
  grep -rn -E '(sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' \
    --include='*' --exclude-dir=.git --exclude-dir=node_modules . 2>/dev/null | head -5 | sed 's/^/    /' || echo "    no matches"
fi
echo "- pre-commit hook present: $([ -f .git/hooks/pre-commit ] && echo yes || echo no)"
echo

# ─────────────────────────────────────────── 7. LAYER TELEMETRY
echo "## 7. Layer telemetry — did it ever fire?"
echo
SLUG="$(echo "$ROOT" | sed 's|/|-|g')"
TDIR="$HOME/.claude/projects/$SLUG"
if [ -d "$TDIR" ]; then
  echo "transcripts: \`$TDIR\` ($(ls -1 "$TDIR"/*.jsonl 2>/dev/null | wc -l | tr -d ' ') sessions)"
else
  TDIR=""
  echo "transcripts: н/п (no transcript dir for this repo — telemetry limited to git)"
fi
echo
# Structural markers, not bare names: a bare name like "qa" matches thousands of unrelated
# tokens. Rules are injected by PATH; skills/agents appear as invocation fields.
echo '| layer artefact | invocations | sessions | last git touch |'
echo '|---|---|---|---|'
for d in .claude/rules .claude/skills .claude/agents; do
  [ -d "$d" ] || continue
  find "$d" -maxdepth 2 -name '*.md' 2>/dev/null | while IFS= read -r f; do
    base=$(basename "$(dirname "$f")"); name=$(basename "$f" .md)
    [ "$name" = "SKILL" ] && name="$base"
    case "$d" in
      *rules)  pat="rules/$name\.md" ;;
      *skills) pat="\"skill\":\"$name\"|/$name\b|skills/$name/" ;;
      *agents) pat="\"subagent_type\":\"$name\"|agents/$name\.md" ;;
    esac
    if [ -n "$TDIR" ]; then
      hits=$(grep -ohE -- "$pat" "$TDIR"/*.jsonl 2>/dev/null | wc -l | tr -d ' ')
      sess=$(grep -lE -- "$pat" "$TDIR"/*.jsonl 2>/dev/null | wc -l | tr -d ' ')
    else hits="?"; sess="?"; fi
    gt=$(git log -1 --format=%ad --date=short -- "$f" 2>/dev/null || echo "—")
    echo "| \`$f\` | $hits | $sess | ${gt:-—} |"
  done
done
echo
echo "> Caveat: this counts INVOCATION markers (rule paths, skill/agent invocation fields)."
echo "> A rule can shape behaviour without its path being echoed, and a session that only"
echo "> DISCUSSED an artefact counts too. Read 0/low as a QUESTION (is its trigger reachable?),"
echo "> not a verdict — lens 4 exists to make that call."
echo

# ─────────────────────────────────────────── 8. reproducibility & debt
echo "## 8. Reproducibility & debt signals"
echo
for f in requirements.txt package.json pyproject.toml Makefile Dockerfile docker-compose.yml .python-version .nvmrc; do
  [ -e "$f" ] && echo "- \`$f\` present"
done
if [ -f requirements.txt ]; then
  tot=$(grep -c -v '^\s*#\|^\s*$' requirements.txt); pin=$(grep -c '==' requirements.txt)
  echo "- requirements.txt: $pin/$tot pinned"
fi
echo "- TODO/FIXME/HACK/XXX in tracked files: $(grep -rn -E 'TODO|FIXME|HACK|XXX' --exclude-dir=.git --exclude-dir=node_modules . 2>/dev/null | wc -l | tr -d ' ')"
echo "- executable scripts: $(find_src -type f \( -name '*.sh' -o -name '*.py' \) | wc -l | tr -d ' ')"
echo
echo "_End of collected facts. Everything above is measured; interpretation is the auditor's job._"
