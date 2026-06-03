"""Configuration for the usage telemetry aggregator.

Tunable constants. Edit and re-run aggregate_usage.py. Imported by it.
"""

# Paths auto-loaded into context by hooks or Claude Code core.
# Read tool calls on these are usually orientation/checking, not deliberate use,
# so they're excluded from the "hot files" ranking.
# Matched as glob patterns against the absolute path.
MECHANICAL_PATHS = [
    "*/MEMORY.md",
    "*/CLAUDE.md",
    "*/knowledge/index.md",
    "*/knowledge/log.md",
    "*/.claude/rules/*.md",
    "*/.claude/CLAUDE.md",
    "*/next-session-prompt.md",
]

# Burst detection: more than BURST_THRESHOLD tool calls on the same (tool, target)
# within BURST_WINDOW_MINUTES minutes are collapsed (only the first BURST_THRESHOLD
# are kept). This reflects single-task multi-edit work, not repeated independent uses.
BURST_WINDOW_MINUTES = 10
BURST_THRESHOLD = 3

# Output caps
TOP_HOT_FILES = 15
TOP_COLD_CANDIDATES = 15
TOP_EDITS = 15
TOP_SKILLS = 10
TOP_TOOLS = 10
TOP_BASH_COMMANDS = 10
