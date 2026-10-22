# Wall time of the SessionEnd hook command (from hooks.json) with stdin left OPEN (nothing written, never closed).
import json, os, subprocess, sys, tempfile, time
plugin = sys.argv[1]
cmd = json.load(open(os.path.join(plugin, "hooks/hooks.json")))["hooks"]["SessionEnd"][0]["hooks"][0]["command"]
repo = tempfile.mkdtemp(); os.makedirs(os.path.join(repo, ".claude/memory")); open(os.path.join(repo, ".claude/memory/MEMORY.md"), "w").write("# x\n")
env = dict(os.environ, CLAUDE_PROJECT_DIR=repo, CLAUDE_PLUGIN_ROOT=plugin)
times = []
for _ in range(int(sys.argv[2]) if len(sys.argv) > 2 else 5):
    t = time.time()
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    p.wait(timeout=10)
    times.append(time.time() - t)
    p.stdin.close()
print("open-stdin runs:", ["%.3f" % x for x in times], "max %.3f" % max(times))
