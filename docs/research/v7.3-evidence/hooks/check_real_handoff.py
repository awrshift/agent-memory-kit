# Feeds a real handoff through session-start (unsplit) and checks its opening section arrives whole.
import json, os, re, subprocess, sys
repo, plugin = sys.argv[1], sys.argv[2]
h = [f for f in os.listdir(os.path.join(repo, "context/handoffs"))][0]
text = open(os.path.join(repo, "context/handoffs", h)).read()
m = re.search(r"(?mi)^##\s+.*opening.*$", text)
opening = text[m.start():].rstrip()
env = dict(os.environ, CLAUDE_PROJECT_DIR=repo, CLAUDE_PLUGIN_ROOT=plugin)
out = subprocess.run(["python3", os.path.join(plugin, "hooks/session-start.py")], input='{"source":"startup"}',
                     capture_output=True, text=True, env=env).stdout
ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
print("handoff chars", len(text), "opening chars", len(opening), "opening whole in context:", opening in ctx)
