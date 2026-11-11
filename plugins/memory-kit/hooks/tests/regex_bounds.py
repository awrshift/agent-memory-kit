"""The repeat bounds of a compiled pattern — one walker shared by the bound tests of hooks/tests and scripts/tests.

`repeats(pattern)` lists every (min, max) repeat bound, nested groups and branches included; a max equal to
`UNBOUNDED` is an unbounded repeat (`*`, `+`, `{n,}`). The walk reads CPython's PRIVATE regex parser (`re._parser`
from Python 3.11, `sre_parse` before). When a Python lacks it, or it lacks the names used here, `PARSER` is None and
each bound test skips with `SKIP_REASON` instead of failing at import. Not a test file: imported, never collected.
"""

from __future__ import annotations

try:
    from re import _parser as PARSER
except ImportError:  # pragma: no cover
    try:
        import sre_parse as PARSER
    except ImportError:
        PARSER = None
if PARSER is not None and not all(hasattr(PARSER, name) for name in
                                  ("parse", "SubPattern", "MAX_REPEAT", "MIN_REPEAT", "MAXREPEAT")):
    PARSER = None  # pragma: no cover
SKIP_REASON = ("no usable private regex parser (re._parser / sre_parse) in this Python: the repeat bounds of a "
               "pattern cannot be read")
UNBOUNDED = PARSER.MAXREPEAT if PARSER is not None else None


def repeats(pattern) -> list[tuple[int, int]]:
    """Every (min, max) repeat bound in a compiled pattern, nested groups and branches included."""
    found = []

    def walk(node):
        if isinstance(node, (list, tuple, PARSER.SubPattern)):
            for item in node:
                walk(item)
        if isinstance(node, tuple) and len(node) == 2 and node[0] in (PARSER.MAX_REPEAT, PARSER.MIN_REPEAT):
            found.append(tuple(node[1][:2]))

    walk(PARSER.parse(pattern.pattern, pattern.flags))
    return found
