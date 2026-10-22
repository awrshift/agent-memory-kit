# The spec's Gates size loop: every source x part, chars of additionalContext (UTF-16 units), each must be <= 10,000.
import json, os, subprocess, sys
plugin, repo = sys.argv[1], sys.argv[2]
env = dict(os.environ, CLAUDE_PROJECT_DIR=repo, CLAUDE_PLUGIN_ROOT=plugin)
worst = 0; rows = []
for s in ("startup", "resume", "compact", "fork", "clear"):
    sizes = []
    for p in range(1, 7):
        out = subprocess.run(["python3", os.path.join(plugin, "hooks/session-start.py"), "--part", str(p)],
                             input=json.dumps({"source": s, "session_id": "gate"}), capture_output=True, text=True, env=env)
        assert out.returncode == 0, out.stderr
        n = len(json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"].encode("utf-16-le")) // 2 if out.stdout.strip() else 0
        sizes.append(n); worst = max(worst, n)
    rows.append("%-8s %s" % (s, sizes))
print("\n".join(rows)); print("max part:", worst, "OK" if worst <= 10000 else "OVER")
