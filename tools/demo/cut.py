#!/usr/bin/env python3
"""Collapse the model's thinking time out of a VHS recording.

VHS records in real time, and a session with three model turns is ~2 minutes of mostly
spinner. This keeps every frame where something the viewer should see changed — output
appearing, the screen scrolling, keystrokes in the input line — plus a short hold after each
change so text can be read, and drops the rest. The spinner/token-counter line just above the
input box is ignored on purpose; it changes every second and would keep every idle stretch.

usage: python3 tools/demo/cut.py demo.mp4 out-stem [--hold 1.8] [--fps 10] [--width 1000] [--tail 4]
       → out-stem.mp4 and out-stem.gif (1000 px wide, 128-colour palette)

Needs ffmpeg, Pillow, numpy. Band boundaries assume the tape's 1280×760 frame.
"""
import argparse, glob, os, shutil, subprocess, sys
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out")
ap.add_argument("--hold", type=float, default=1.8, help="seconds kept after the last change")
ap.add_argument("--fps", type=int, default=10)
ap.add_argument("--tail", type=float, default=4.0, help="seconds to hold the final frame")
ap.add_argument("--width", type=int, default=1000, help="GIF width in px")
a = ap.parse_args()

work = a.out + ".frames"; sel = a.out + ".sel"
for d in (work, sel):
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-vf", f"fps={a.fps}", f"{work}/%05d.png"], check=True)

files = sorted(glob.glob(f"{work}/*.png")); prev = None; events = []
for f in files:
    img = np.asarray(Image.open(f).convert("L"), dtype=np.int16)
    if prev is None:
        events.append(True); prev = img; continue
    d = np.abs(img - prev) > 40
    main = d[:590].sum()          # output area
    inp = d[655:700].sum()        # the input line (keystrokes)
    events.append(main > 300 or inp > 80)   # rows 590–655 = spinner + token counter: ignored
    prev = img

hold = int(a.hold * a.fps); keep = []; since = 10**9
for i, e in enumerate(events):
    since = 0 if e else since + 1
    if since <= hold:
        keep.append(i)
keep += [len(files) - 1] * int(a.tail * a.fps)
for j, i in enumerate(keep):
    os.link(files[i], f"{sel}/{j+1:05d}.png")
print(f"frames {len(files)} → kept {len(keep)} ({len(keep)/a.fps:.1f}s), events {sum(events)}", file=sys.stderr)

subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", f"{sel}/%05d.png",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", a.out + ".mp4"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", f"{sel}/%05d.png", "-vf",
                f"scale={a.width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
                a.out + ".gif"], check=True)
shutil.rmtree(work); shutil.rmtree(sel)
