#!/usr/bin/env python3
"""Regenerate a README diagram, using the existing asset as a style reference so the new
panel matches the rest of the set.

usage:  GOOGLE_API_KEY=... python3 tools/genimg.py <ref.png|-> <prompt-file> <out.png> [model]

The prompt file must carry the COMPLETE text spec of the diagram, every string verbatim.
Asking the model to "reproduce this exactly and change only X" reliably drifts the spelling
of words it is not thinking about — see docs/ASSETS.md. Always look at the result before
committing it.
"""
import base64, json, os, sys, urllib.request, urllib.error

MODEL = sys.argv[4] if len(sys.argv) > 4 else "gemini-3-pro-image"
KEY = os.environ["GOOGLE_API_KEY"]
ref, prompt_file, out = sys.argv[1], sys.argv[2], sys.argv[3]

prompt = open(prompt_file, encoding="utf-8").read()
parts = [{"text": prompt}]
if ref != "-":
    parts.insert(0, {"inline_data": {"mime_type": "image/png",
                                     "data": base64.b64encode(open(ref, "rb").read()).decode()}})

body = {
    "contents": [{"role": "user", "parts": parts}],
    "generationConfig": {
        "responseModalities": ["IMAGE"],
        "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"},
    },
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    resp = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:800]); sys.exit(1)

wrote = False
for cand in resp.get("candidates", []):
    for p in cand.get("content", {}).get("parts", []):
        d = p.get("inlineData") or p.get("inline_data")
        if d:
            open(out, "wb").write(base64.b64decode(d["data"]))
            print("wrote", out, os.path.getsize(out), "bytes"); wrote = True
        elif p.get("text"):
            print("model text:", p["text"][:300])
if not wrote:
    print("NO IMAGE RETURNED:", json.dumps(resp)[:600])
    sys.exit(2)
