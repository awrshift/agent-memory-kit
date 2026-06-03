"""Path constants for the knowledge base scripts."""

from pathlib import Path
from datetime import datetime, timezone

# Root = project root (config.py lives at .claude/memory/scripts/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Knowledge base — single subdir.
# concepts/ = topical articles compiled from daily/*.md by /memory-compile.
MEMORY_DIR = ROOT_DIR / ".claude" / "memory"
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"
INDEX_FILE = KNOWLEDGE_DIR / "index.md"
LOG_FILE = KNOWLEDGE_DIR / "log.md"

# Raw sources
DAILY_DIR = ROOT_DIR / "daily"

# Per-project scope
PROJECTS_DIR = ROOT_DIR / "projects"

# State tracking (runtime state in .claude/state/, gitignored)
SCRIPTS_DIR = Path(__file__).resolve().parent
STATE_DIR = ROOT_DIR / ".claude" / "state"
STATE_FILE = STATE_DIR / "compile-state.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
