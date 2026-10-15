"""Trace the two-line "Koolabung / Lures" wordmark, one line at a time.

Usage: python trace_wordmark.py <wordmark.bmp> <out.json>
Needs numpy, scipy, opencv-python-headless, and potrace on PATH.

Writes JSON with, per line, a potrace path (in source pixels once its
transform is applied) and its ink box, so the layout can set the lines'
alignment independently.
"""
import json
import re
import subprocess
import sys
import tempfile

import cv2
import numpy as np
from scipy import ndimage as ndi

UPSCALE = 4
SMOOTH = 1.25  # blur sigma in source px before thresholding

src, out = sys.argv[1], sys.argv[2]
grey = cv2.imread(src, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
ink = grey < 0.6

# Assign each glyph (connected component) to a line by where its top sits.
lab, n = ndi.label(ink)
tops = ndi.find_objects(lab)
split = ink.shape[0] / 2
lines = {"line1": np.zeros_like(ink), "line2": np.zeros_like(ink)}
for k, sl in enumerate(tops, start=1):
    key = "line1" if sl[0].start < split else "line2"
    lines[key] |= lab == k

result = {}
for key, mask in lines.items():
    # Smooth from the continuous grey image, limited to this line's glyphs.
    near = cv2.resize(ndi.binary_dilation(mask, iterations=3).astype(np.float32), None,
                      fx=UPSCALE, fy=UPSCALE, interpolation=cv2.INTER_NEAREST) > 0.5
    big = cv2.resize(1 - grey, None, fx=UPSCALE, fy=UPSCALE, interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), UPSCALE * SMOOTH)
    big = (big > 0.5) & near
    with tempfile.NamedTemporaryFile(suffix=".pbm") as f:
        cv2.imwrite(f.name, np.where(big, 0, 255).astype(np.uint8))
        svg = subprocess.run(
            ["potrace", "-s", "--flat", "-t", "40", "-a", "0.6", "-O", "2.0", "-o", "-", f.name],
            check=True, capture_output=True, text=True,
        ).stdout
    g = re.search(r'<g transform="([^"]+)"[^>]*>(.*)</g>', svg, re.S)
    d = " ".join(" ".join(x.split()) for x in re.findall(r'd="([^"]+)"', g.group(2)))
    ys, xs = np.nonzero(mask)
    result[key] = {
        "transform": f"scale({1 / UPSCALE}) {g.group(1)}",
        "d": d,
        "box": [int(xs.min()), int(ys.min()), int(xs.max() + 1 - xs.min()), int(ys.max() + 1 - ys.min())],
    }

json.dump(result, open(out, "w"))
for key, v in result.items():
    print(key, v["box"])
