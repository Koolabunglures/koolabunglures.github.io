"""Derive single-shape artwork from a composed logo SVG by rendering and tracing it.

Usage:
  python trace_shape.py one-colour <in.svg> <out.svg> --fill "#64348A"
  python trace_shape.py cut-contour <in.svg> <out.svg>
Needs numpy, scipy, opencv-python-headless, and potrace and rsvg-convert on PATH.

one-colour   every inked (non-white) area as one flat colour, white areas as
             holes: artwork for plotter-cut vinyl in a single colour
cut-contour  a copy of <in.svg> with a contour-cut line round its outer edge,
             stroked in CUT_RGB so cmyk_pdf.py can turn it into the
             "CutContour" spot colour that print-and-cut RIPs look for
"""
import argparse
import re
import subprocess
import tempfile

import cv2
import numpy as np
from scipy import ndimage as ndi

RENDER_WIDTH = 8000  # px; the logo is ~1800 units wide
CUT_RGB = "#FF00FF"
CUT_WIDTH_MM = 0.1
INK_LUMINANCE = 0.85  # brighter than this counts as white

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["one-colour", "cut-contour"])
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--fill", default="#000000")
args = ap.parse_args()

svg = open(args.src).read()
vx, vy, vw, vh = map(float, re.search(r'viewBox="([^"]+)"', svg).group(1).split())
width_mm = float(re.search(r'width="([\d.]+)mm"', svg).group(1))

with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["rsvg-convert", "-w", str(RENDER_WIDTH), args.src, "-o", f"{tmp}/r.png"], check=True)
    rgba = cv2.imread(f"{tmp}/r.png", cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    alpha = rgba[..., 3]
    px_per_unit = rgba.shape[1] / vw

    if args.mode == "one-colour":
        lum = rgba[..., :3] @ np.array([0.114, 0.587, 0.299], np.float32)  # BGR
        mask = (alpha > 0.5) & (lum < INK_LUMINANCE)
        turd = 40
    else:
        # Outer edge only: a plotter cutting inner holes leaves pieces to weed.
        mask = ndi.binary_fill_holes(alpha > 0.5)
        mask = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 6) > 0.5
        turd = 2000
    cv2.imwrite(f"{tmp}/m.pbm", np.where(mask, 0, 255).astype(np.uint8))
    traced = subprocess.run(
        ["potrace", "-s", "--flat", "-t", str(turd), "-a", "1.2", "-O", "0.5", "-o", "-", f"{tmp}/m.pbm"],
        check=True, capture_output=True, text=True,
    ).stdout

g = re.search(r'<g transform="([^"]+)"[^>]*>(.*)</g>', traced, re.S)
d = " ".join(" ".join(x.split()) for x in re.findall(r'd="([^"]+)"', g.group(2)))
transform = f"translate({vx},{vy}) scale({1 / px_per_unit:.6f}) {g.group(1)}"

if args.mode == "one-colour":
    head = re.match(r"(<svg[^>]*>)", svg).group(1)
    out = (f'{head}<title>Koolabung Lures</title>'
           f'<path fill="{args.fill}" transform="{transform}" d="{d}"/></svg>\n')
else:
    # Stroke widths scale with the path's transform, so give it in final units.
    unit_mm = width_mm / vw
    path_scale = 1 / px_per_unit * 0.1  # potrace's own transform is scale(0.1,-0.1)
    sw = CUT_WIDTH_MM / unit_mm / path_scale
    cut = (f'<path id="CutContour" fill="none" stroke="{CUT_RGB}" stroke-width="{sw:.2f}" '
           f'transform="{transform}" d="{d}"/>')
    out = svg.replace("</svg>", cut + "</svg>")
open(args.out, "w").write(out)
