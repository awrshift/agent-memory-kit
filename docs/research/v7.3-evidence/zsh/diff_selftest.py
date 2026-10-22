import importlib.util, sys
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
src = load("src", "~/dev/project-01/.claude/hooks/zsh-split-guard.py")
port = load("port", "~/dev/claude-memory-kit-v73-zsh/plugins/memory-kit/hooks/guard-zsh-split.py")
bad = 0
for cmd, expect in src.SELFTEST:
    got = bool(port.check(cmd))
    if got != expect:
        bad += 1; print("MISMATCH", expect, got, repr(cmd), port.check(cmd))
print("selftest cases", len(src.SELFTEST), "port disagrees with expected:", bad)
