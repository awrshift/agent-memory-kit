"""Counts for the S2 report: corpus FP/miss of the port, port-vs-source agreement, worst-case timings."""
import importlib.util, json, os, subprocess, sys, time
sys.path.insert(0, "~/dev/claude-memory-kit-v73-zsh/plugins/memory-kit/hooks/tests")
os.chdir("~/dev/claude-memory-kit-v73-zsh")
import test_guard_zsh_split as T
spec = importlib.util.spec_from_file_location("src", "~/dev/project-01/.claude/hooks/zsh-split-guard.py")
src = importlib.util.module_from_spec(spec); spec.loader.exec_module(src)
for label, cases in (("source selftest", T.SOURCE_CASES), ("hand corpus", T.CORPUS)):
    neg = [c for c, b in cases if not b]; pos = [c for c, b in cases if b]
    fp = [c for c in neg if T.G.check(c)]; miss = [c for c in pos if not T.G.check(c)]
    sfp = [c for c in neg if src.check(c)]; smiss = [c for c in pos if not src.check(c)]
    disagree = [c for c, _ in cases if bool(T.G.check(c)) != bool(src.check(c))]
    print(f"{label}: n={len(cases)} legit={len(neg)} defects={len(pos)} | port FP={len(fp)} miss={len(miss)} | source FP={len(sfp)} miss={len(smiss)} | port!=source {len(disagree)}")
    for c in disagree: print("   disagree:", repr(c), "port", T.G.check(c), "source", src.check(c))
n = 100_000
cases = {
 "unclosed dq": 'a="x y"; set -- $a "' + "ab" * (n // 2),
 "$a x50k set": 'a="x y"; set -- ' + "$a" * (n // 2),
 "$( x50k": "$(" * (n // 2),
 "${a x33k": "${a" * (n // 3),
 "quoted items": "for x in " + '"a b" ' * (n // 6) + "; do set -- $x; done",
}
for label, cmd in cases.items():
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    t0 = time.monotonic(); r = subprocess.run(T.COMMAND, shell=True, input=payload, capture_output=True, text=True, env=T.BASE_ENV); dt = time.monotonic() - t0
    print(f"worst case {label}: len={len(cmd)} exit={r.returncode} {dt:.3f}s out={r.stdout[:80]!r}")
