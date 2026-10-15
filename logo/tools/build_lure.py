"""Trace the layer masks from separate.py and assemble the vector lure.

Usage: python build_lure.py <layerdir> <out.svg>
Needs potrace on PATH.

The swoosh is drawn from the fitted ellipses rather than traced, and the body
gets a linear gradient from the sampled colours; every other layer is a
flat-colour potrace trace.
"""
import json
import math
import re
import subprocess
import sys

UPSCALE = 4

layerdir, out = sys.argv[1], sys.argv[2]
# Thinnest point of the swoosh as a fraction of its thickest. The original
# tapers to a hairline that would vanish on a hull; None keeps it as fitted.
SWOOSH_MIN_RATIO = 0.25
p = json.load(open(f"{layerdir}/params.json"))
W, H = p["size"]

FILLS = {
    "bib": "#FFFFFF",
    "mouth": p["mouth_colour"],
    "body_white": "#FFFFFF",
    "red": p["red_colour"],
    "grey": p["grey_colour"],
    "black": "#18171A",
}


def trace(name):
    svg = subprocess.run(
        ["potrace", "-s", "--flat", "-t", "10", "-a", "1.1", "-O", "1.0", "-o", "-", f"{layerdir}/{name}.pbm"],
        check=True, capture_output=True, text=True,
    ).stdout
    g = re.search(r'<g transform="([^"]+)"[^>]*>(.*)</g>', svg, re.S)
    paths = re.findall(r'd="([^"]+)"', g.group(2))
    d = " ".join(" ".join(x.split()) for x in paths)
    return f'<path transform="scale({1 / UPSCALE}) {g.group(1)}" d="{d}"/>'


def ellipse_points(e, n=720):
    a = math.radians(e["angle"])
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x, y = e["rx"] * math.cos(t), e["ry"] * math.sin(t)
        pts.append((e["cx"] + x * math.cos(a) - y * math.sin(a), e["cy"] + x * math.sin(a) + y * math.cos(a)))
    return pts


def thickness_range(o, i):
    inner = ellipse_points(i, 360)
    ds = [min(math.dist(q, r) for r in inner) for q in ellipse_points(o, 180)]
    return min(ds), max(ds)


def thicken(o, i):
    """Move the inner ellipse's centre towards the outer's and shrink it so the
    thick side keeps its width and the thin side reaches SWOOSH_MIN_RATIO of it."""
    _, t_max = thickness_range(o, i)
    best = None
    for f in [x / 40 for x in range(41)]:
        for extra in [x / 2 for x in range(0, 41)]:
            c = dict(i)
            c["cx"] = o["cx"] + f * (i["cx"] - o["cx"])
            c["cy"] = o["cy"] + f * (i["cy"] - o["cy"])
            c["rx"], c["ry"] = i["rx"] - extra, i["ry"] - extra
            lo, hi = thickness_range(o, c)
            err = (hi - t_max) ** 2 + (lo - SWOOSH_MIN_RATIO * t_max) ** 2
            if best is None or err < best[0]:
                best = (err, c)
    return best[1]


def swoosh():
    o, i = p["ring_outer"], p["ring_inner"]
    if SWOOSH_MIN_RATIO is not None:
        i = thicken(o, i)
    return (
        f'<path fill="{p["ring_colour"]}" fill-rule="evenodd" d="'
        f'{ellipse_path_rot(o)} {ellipse_path_rot(i)}"/>'
    )


def ellipse_path_rot(e):
    a = math.radians(e["angle"])
    cx, cy, rx, ry = e["cx"], e["cy"], e["rx"], e["ry"]
    x0, y0 = cx - rx * math.cos(a), cy - rx * math.sin(a)
    x1, y1 = cx + rx * math.cos(a), cy + rx * math.sin(a)
    return (f"M{x0:.2f},{y0:.2f} A{rx:.2f},{ry:.2f} {e['angle']:.3f} 1,0 {x1:.2f},{y1:.2f} "
            f"A{rx:.2f},{ry:.2f} {e['angle']:.3f} 1,0 {x0:.2f},{y0:.2f}Z")


gr = p["gradient"]
stops = "".join(f'<stop offset="{s["offset"]}" stop-color="{s["colour"]}"/>' for s in gr["stops"])
defs = (f'<linearGradient id="body" gradientUnits="userSpaceOnUse" '
        f'x1="{gr["from"][0]:.1f}" y1="{gr["from"][1]:.1f}" x2="{gr["to"][0]:.1f}" y2="{gr["to"][1]:.1f}">'
        f"{stops}</linearGradient>")

parts = [swoosh()]
for name in ["bib", "body", "mouth", "body_white", "ellipses", "grey", "black"]:
    if name == "ellipses":
        for e in p["ellipses"]:
            parts.append(f'<path fill="{FILLS[e["layer"]]}" d="{ellipse_path_rot(e)}"/>')
        continue
    if name == "body":
        # A gradient on the traced path would be laid out in potrace's flipped
        # coordinate space, so paint a page-space rect clipped to the body.
        defs += f'<clipPath id="body-clip">{trace(name)}</clipPath>'
        parts.append(f'<rect id="lure-body" width="{W}" height="{H}" fill="url(#body)" clip-path="url(#body-clip)"/>')
    else:
        parts.append(f'<g id="lure-{name.replace("_", "-")}" fill="{FILLS[name]}">{trace(name)}</g>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<!-- swoosh-outer {json.dumps(p["ring_outer"])} -->'
       f"<defs>{defs}</defs>" + "".join(parts) + "</svg>\n")
open(out, "w").write(svg)
