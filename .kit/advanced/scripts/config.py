"""Path constants for the knowledge base scripts (lint.py).

Works from both locations: .kit/advanced/scripts/ (as shipped) and
.claude/memory/scripts/ (after the documented enable copy) — both sit
exactly four levels below the project root.
"""

from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Knowledge base — single subdir of topical articles, written by the agent
# during /close-session on the user's verbal "yes".
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"


def today_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
