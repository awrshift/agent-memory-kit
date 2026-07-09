#!/usr/bin/env python3
"""One-off Nano Banana Pro image generator for the claude-memory-kit README assets.
Key resolution mirrors ~/.claude/skills/dont-ask-me/scripts/gemini.py: GOOGLE_API_KEY env
var first, else ~/.gemini/api_key. Model discovered at runtime, pinned to the stable
'gemini-3-pro-image' (Nano Banana Pro, non-preview) id.
"""
import base64
import os
import sys

from google import genai
from google.genai import types

MODEL = "models/gemini-3-pro-image"

GLOBAL_KEY_FILE = os.path.expanduser("~/.gemini/api_key")


def resolve_api_key():
    env_key = os.environ.get("GOOGLE_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    try:
        with open(GLOBAL_KEY_FILE, encoding="utf-8") as fh:
            return fh.read().strip() or None
    except OSError:
        return None


NEGATIVE = (
    " Strict negative constraints: no indigo or purple, no #6366F1, no neon flood, "
    "no glassmorphism, no glowing neon card borders, no bento grid layout, no plastic-smooth "
    "3D renders, no stock-photo people, no generic AI particle network cliche, no blue-black "
    "cyberpunk tone."
)

STYLE = (
    "Warm charcoal background color #17150F (olive-tinted, never blue-black). "
    "Warm off-white ink color #F1ECDF for any implied text areas. ONE acid lime-chartreuse "
    "accent color #CFEF4A used only for active/awake/live elements. A second warm amber "
    "color #E08A4A used only for dormant/inactive/cold elements — never decorative, never "
    "mixed with lime on the same shape. Structural lines in dark olive #55503E, thin and "
    "sparse. Subtle film grain texture over the whole image. Editorial, generous negative "
    "space, asymmetric composition — not centered, not symmetric. No embedded text, no "
    "letters, no words, no numbers anywhere in the image — pure abstract/illustrative "
    "artwork only, background art for a designer to place typography on top of afterward."
    + NEGATIVE
)

PROMPTS = {
    "og-banner-art": (
        "An abstract organism made of asymmetric jittered nodes connected by thin curved "
        "threads, like a living neural/root structure but hand-drawn and organic, not a "
        "geometric wireframe. A dense bright lime-chartreuse core cluster at the right side "
        "of frame with tight glowing nodes, transitioning outward through a sparser ring of "
        "warm amber dim nodes at the outer edge, representing 'hot memory awake' at center "
        "vs 'cold memory dormant' at the periphery. Wide 16:9 cinematic composition, the "
        "organism occupies the right half of the frame, left half is empty warm charcoal "
        "negative space for a designer to place a headline. " + STYLE
    ),
    "01-art": (
        "A wide 16:9 abstract composition split into two symmetric halves by a thin vertical "
        "dark olive line. The left half is rendered in dim, muted warm amber tones with a "
        "single small dormant amber node/circle, evoking 'cold, stuck, repeating the same "
        "state'. The right half is rendered with a single bright lime-chartreuse glowing node "
        "with faint radiating threads, evoking 'awake, continuous, alive'. Warm charcoal base "
        "background throughout, generous empty space top and bottom for a designer to place "
        "headline and body text. " + STYLE
    ),
    "02-art": (
        "A wide 16:9 abstract composition showing four loose organic node-clusters arranged "
        "in a gentle left-to-right arc across the lower third of the frame, connected by thin "
        "curved dark-olive threads suggesting a sequence or journey. The first two clusters "
        "glow warm lime-chartreuse (active), the third cluster is a brighter lime pulse, the "
        "fourth cluster is dim warm amber (waiting/dormant until tomorrow). A faint looping "
        "curved thread connects the last cluster back toward the first, very subtle. Warm "
        "charcoal background, plenty of empty space in the upper two-thirds for a designer to "
        "place a large headline. " + STYLE
    ),
    "03-art": (
        "A wide 16:9 abstract composition with four vertical loose organic node-clusters "
        "evenly spaced across the frame like four separate small plants or root systems "
        "growing upward from a thin dark-olive baseline near the bottom. The leftmost cluster "
        "glows brightest lime-chartreuse (most active), the other three clusters are rendered "
        "in warm off-white and muted amber tones at lower brightness (steady, less active but "
        "not fully dormant). Warm charcoal background, generous empty space above each "
        "cluster for a designer to place labels. " + STYLE
    ),
    "04-art": (
        "A wide 16:9 abstract composition showing a single organic thread flowing left to "
        "right through four loose node-clusters like stepping stones, depicting a "
        "transformation journey. The first cluster is dim warm amber (a faint first spark), "
        "the second cluster is amber mixed with a little lime (gaining strength), the third "
        "cluster is bright lime with a small radiant burst (a decisive moment), the fourth "
        "cluster is solid dense lime-chartreuse (permanent, fully formed). Warm charcoal "
        "background, thin dark-olive connecting threads, generous empty space top and bottom "
        "for a designer to place headline and captions. " + STYLE
    ),
    "05-art": (
        "A wide 16:9 abstract composition, asymmetric editorial layout. On the left third, a "
        "loose organic branching root/tree structure in warm off-white and lime-chartreuse "
        "with one branch highlighted brighter lime than the others (one branch selected among "
        "several). On the right third, four thin horizontal dark-olive-outlined bands stacked "
        "vertically, softly lime-lit, evoking shared always-on layers. Warm charcoal "
        "background, wide empty middle and top area for a designer to place headline and "
        "captions. " + STYLE
    ),
    "06-art": (
        "A wide 16:9 abstract composition split into a soft left/right editorial layout by "
        "generous negative space, not a hard line. On the left, five thin horizontal dark-"
        "olive threads stacked like calm sound-waves, each with a tiny dim lime pulse node, "
        "evoking quiet automatic background processes. On the right, two small bright "
        "lime-chartreuse glowing clusters, evoking deliberate user-invoked actions. Warm "
        "charcoal background throughout, generous empty space for a designer to place a "
        "headline and labeled rows. " + STYLE
    ),
}


def gen(client, key, out_path, aspect="16:9", size="2K"):
    prompt = PROMPTS[key]
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size),
        ),
    )
    saved = False
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                data = part.inline_data.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                with open(out_path, "wb") as fh:
                    fh.write(data)
                saved = True
                print(f"saved {out_path} ({len(data)} bytes)")
    if not saved:
        print(f"NO IMAGE returned for {key}: {resp}", file=sys.stderr)
    return saved


def main():
    keys = sys.argv[1:] or list(PROMPTS.keys())  # capture BEFORE client init — genai/grpc/absl mutates sys.argv as a side effect
    api_key = resolve_api_key()
    if not api_key:
        print("ERROR: no API key found", file=sys.stderr)
        sys.exit(1)
    client = genai.Client(api_key=api_key)
    print(f"using model {MODEL}")
    out_dir = os.path.join(os.path.dirname(__file__), "gen")
    os.makedirs(out_dir, exist_ok=True)
    for k in keys:
        out_path = os.path.join(out_dir, f"{k}.png")
        ok = gen(client, k, out_path)
        if not ok:
            print(f"FAILED: {k}")


if __name__ == "__main__":
    main()
