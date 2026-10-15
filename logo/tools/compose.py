"""Lay out the traced wordmark and the vector lure as one logo.

Usage: python compose.py <wordmark.json> <lure.svg> <out.svg>
           [--lure-scale 0.9] [--align right] [--outline] [--width-mm 1000]
           [--parts both|lure|text]

  --lure-scale  lure-and-swoosh height as a multiple of the two-line text height
  --align       "left" or "right": how "Lures" sits under "Koolabung"
  --outline     add a white outline round the text and a white fill inside the
                swoosh, for dark hulls
  --parts       draw the whole logo, or only the lure or only the wordmark; the
                layout is the same, the page is trimmed to what is drawn
  --width-mm    physical width of the whole logo written into the SVG (the
                artwork is vector, so this is a nominal size, not a resolution);
                with --parts, the part keeps the size it has in the whole logo

Units inside are source pixels of the wordmark bitmap. The viewBox is trimmed
to the artwork plus a small margin.
"""
import argparse
import json
import re

ap = argparse.ArgumentParser()
ap.add_argument("wordmark")
ap.add_argument("lure")
ap.add_argument("out")
ap.add_argument("--lure-scale", type=float, default=0.9)
ap.add_argument("--align", choices=["left", "right"], default="right")
ap.add_argument("--outline", action="store_true")
ap.add_argument("--width-mm", type=float)
ap.add_argument("--parts", choices=["both", "lure", "text"], default="both")
args = ap.parse_args()

TEXT_PURPLE = "#64348A"
LURE_BOX = (43, 20, 886, 1170)  # ink box of the lure artwork (x, y, w, h)
GAP = 0.10  # between text and lure, as a fraction of text height
MARGIN = 0.06  # as a fraction of text height
# Right-aligned, "Lures" ends under the descender of "g"; open the leading a
# little so they don't crowd. In source px.
RIGHT_ALIGN_EXTRA_LEADING = 28
OUTLINE = 0.045  # white outline width, as a fraction of text height

lines = json.load(open(args.wordmark))
l1, l2 = lines["line1"], lines["line2"]
x1_, y1_, w1, h1 = l1["box"]
x2_, y2_, w2, h2 = l2["box"]
right = args.align == "right"
dx2 = (x1_ + w1) - (x2_ + w2) if right else x1_ - x2_
dy2 = RIGHT_ALIGN_EXTRA_LEADING if right else 0

wx0, wy0 = min(x1_, x2_ + dx2), y1_
wx1, wy1 = max(x1_ + w1, x2_ + dx2 + w2), y2_ + dy2 + h2
wh = wy1 - wy0

lure_src = open(args.lure).read()
lure = re.search(r"<svg[^>]*>(.*)</svg>", lure_src, re.S).group(1)
swoosh_outer = json.loads(re.search(r"<!-- swoosh-outer (.*?) -->", lure_src).group(1))
lx, ly, lw, lh = LURE_BOX
k = args.lure_scale * wh / lh
lw_s, lh_s = lw * k, lh * k
lure_left = wx1 + GAP * wh
lure_top = wy0 + wh / 2 - lh_s / 2
tx, ty = lure_left - lx * k, lure_top - ly * k

show_text, show_lure = args.parts in ("both", "text"), args.parts in ("both", "lure")
boxes = ([(wx0, wy0, wx1, wy1)] if show_text else []) + \
    ([(lure_left, lure_top, lure_left + lw_s, lure_top + lh_s)] if show_lure else [])
m = MARGIN * wh + (OUTLINE * wh if args.outline else 0)
x0, y0 = min(b[0] for b in boxes) - m, min(b[1] for b in boxes) - m
x1, y1 = max(b[2] for b in boxes) + m, max(b[3] for b in boxes) + m
full_w = lure_left + lw_s - wx0 + 2 * m
W, H = x1 - x0, y1 - y0


def line(v, dx, dy, attrs=""):
    return f'<path transform="translate({dx},{dy}) {v["transform"]}" d="{v["d"]}"{attrs}/>'


def path_scale(v):
    """Overall scale of a traced line's own transform, e.g. "scale(0.25) ... scale(0.1,-0.1)"."""
    s = 1.0
    for a in re.findall(r"scale\(([-\d.]+)", v["transform"]):
        s *= abs(float(a))
    return s


word = f'<g id="wordmark" fill="{TEXT_PURPLE}">{line(l1, 0, 0)}{line(l2, dx2, dy2)}</g>'
lure_g = f'<g id="lure" transform="translate({tx:.2f},{ty:.2f}) scale({k:.5f})">{lure}</g>'

underlay = ""
if args.outline:
    sw = OUTLINE * wh * 2  # stroke is centred on the edge
    e = swoosh_outer
    text_under = (
        # Strokes scale with each path's own transform, so undo it.
        f'<g fill="#FFFFFF">'
        f'{line(l1, 0, 0, f' stroke-width="{sw / path_scale(l1):.1f}"')}'
        f'{line(l2, dx2, dy2, f' stroke-width="{sw / path_scale(l2):.1f}"')}</g>'
    )
    lure_under = (
        f'<g transform="translate({tx:.2f},{ty:.2f}) scale({k:.5f})">'
        f'<ellipse cx="{e["cx"]:.2f}" cy="{e["cy"]:.2f}" rx="{e["rx"]:.2f}" ry="{e["ry"]:.2f}" '
        f'transform="rotate({e["angle"]:.3f} {e["cx"]:.2f} {e["cy"]:.2f})" stroke-width="{sw / k:.1f}"/>'
        f'<use href="#lure-black" stroke-width="{sw / k:.1f}"/>'
        "</g>"
    )
    underlay = (
        f'<g id="outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="{sw:.1f}" stroke-linejoin="round">'
        f'{text_under if show_text else ""}{lure_under if show_lure else ""}</g>'
    )

if args.width_mm:
    mm = args.width_mm / full_w
    size = f'width="{W * mm:.1f}mm" height="{H * mm:.1f}mm"'
else:
    size = f'width="{W:.0f}" height="{H:.0f}"'

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'viewBox="{x0:.1f} {y0:.1f} {W:.1f} {H:.1f}" {size}>'
    f"<title>Koolabung Lures</title>{underlay}{word if show_text else ''}{lure_g if show_lure else ''}</svg>\n"
)
open(args.out, "w").write(svg)
print(f"{args.out}: {W:.0f} x {H:.0f}  ratio {W / H:.2f}:1")
