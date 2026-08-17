"""Path constants for the knowledge base scripts (lint.py).

v6: the scripts ship inside the plugin, so their own depth says nothing about the repository
being linted — the project root comes from the harness (CLAUDE_PROJECT_DIR), falling back to
the working directory.
"""

import os
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()

# Knowledge base — single subdir of topical articles, written by the agent
# during /close-session on the user's verbal "yes".
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"


def today_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
