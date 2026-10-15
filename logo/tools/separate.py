"""Split the lure-and-swoosh bitmap into per-colour masks for potrace.

Usage: python separate.py <source.bmp> <outdir>
Needs numpy, scipy, opencv-python-headless.

Writes, into <outdir>:
  <layer>.pbm   upscaled, smoothed masks (black = shape) for potrace
  <layer>.png   the same masks at source scale, for eyeballing
  params.json   fitted swoosh ellipses and sampled body gradient colours
"""
import json
import sys

import cv2
import numpy as np
from scipy import ndimage as ndi

UPSCALE = 4
SMOOTH = 1.1  # blur sigma in source px; the source BMP has hard, unantialiased edges

src, outdir = sys.argv[1], sys.argv[2]
bgr = cv2.imread(src, cv2.IMREAD_COLOR)
rgb = bgr[:, :, ::-1].astype(np.float32) / 255
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
mx, mn = rgb.max(-1), rgb.min(-1)
sat = mx - mn

white = mn > 0.92
red = (r > 0.55) & (g < 0.25) & (b < 0.3) & (r - b > 0.35)
coloured = (sat > 0.18) & ~red  # purples and pinks
black = (mx < 0.42) & (sat < 0.12)
grey = (sat < 0.12) & (mx >= 0.42) & ~white


paint = coloured | red



def ellipse_mask(e, grow=0.0):
    m = np.zeros(paint.shape, np.uint8)
    (cx, cy), (w, h), a = e
    cv2.ellipse(m, ((cx, cy), (w + 2 * grow, h + 2 * grow), a), 1, -1)
    return m.astype(bool)


def disk(rad):
    y, x = np.ogrid[-rad:rad + 1, -rad:rad + 1]
    return x * x + y * y <= rad * rad


def robust_fit(pts, tol=2.0):
    """fitEllipse, then refit on the points within tol px of the first fit."""
    pts = np.asarray(pts, np.float32)
    for _ in range(4):
        e = cv2.fitEllipse(pts)
        m = np.zeros((paint.shape[0] + 200, paint.shape[1] + 200), np.uint8)
        (cx, cy), (w, h), a = e
        cv2.ellipse(m, ((cx + 100, cy + 100), (w, h), a), 1, 1)
        dist = ndi.distance_transform_edt(m == 0)
        d = dist[pts[:, 1].astype(int) + 100, pts[:, 0].astype(int) + 100]
        keep = d < max(tol, np.percentile(d, 70))
        if keep.all():
            break
        pts = pts[keep]
    return e


# The swoosh is a crescent between two ellipses. Cast rays inward from well
# outside the artwork towards its centre: the first painted pixel each ray
# meets is on the outer edge, and the end of that painted run, if it is short,
# is on the inner edge. Rays that first hit a hook or ring are dropped by the
# robust fit.
h_, w_ = paint.shape
c0 = np.array([w_ / 2, h_ / 2])
reach = np.hypot(w_, h_) / 2
outer_pts, inner_pts = [], []
for t in np.linspace(0, 2 * np.pi, 720, endpoint=False):
    d = np.array([np.cos(t), np.sin(t)])
    run = []
    for s in np.arange(reach, 0, -0.5):
        x, y = c0 + d * s
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= xi < w_ and 0 <= yi < h_):
            continue
        if coloured[yi, xi]:
            run.append((x, y))
        elif run:
            break
    if run:
        outer_pts.append(run[0])
        if len(run) < 2 * 40:
            inner_pts.append(run[-1])
ring_outer = robust_fit(outer_pts)
ring_inner = robust_fit(inner_pts)
ring = ellipse_mask(ring_outer) & ~ellipse_mask(ring_inner)

body_core = ndi.binary_opening(paint, disk(14))
lab, n = ndi.label(body_core)
sizes = ndi.sum(body_core, lab, range(1, n + 1))
body_core = lab == (1 + int(np.argmax(sizes)))

paint_nr = paint & ~ndi.binary_dilation(ring, disk(2))
body0 = ndi.binary_opening(paint_nr, disk(6))
lab, n = ndi.label(body0)
sizes = ndi.sum(body0, lab, range(1, n + 1))
body0 = lab == (1 + int(np.argmax(sizes)))
body = body0 | (paint_nr & ndi.binary_dilation(body0, disk(6)))
body = body | (white & ndi.binary_dilation(body, disk(8)) & ~ndi.binary_dilation(ring, disk(2)))
body = ndi.binary_fill_holes(ndi.binary_closing(body, disk(10)))
body = ndi.binary_opening(body, disk(4))


def fit(e):
    (cx, cy), (w, h), a = e
    return {"cx": cx, "cy": cy, "rx": w / 2, "ry": h / 2, "angle": a}


# Body gradient: average colour in the top-left and bottom-right of the body
# along the direction of greatest luminance change.
inside = body & (sat > 0.18) & ~red
yy, xx = np.nonzero(inside)
lum = (0.3 * r + 0.59 * g + 0.11 * b)[inside]
A = np.stack([xx, yy, np.ones_like(xx)], 1).astype(np.float64)
coef, *_ = np.linalg.lstsq(A, lum, rcond=None)
direction = coef[:2] / np.linalg.norm(coef[:2])
proj = (np.stack([xx, yy], 1) @ direction)
lo, hi = np.percentile(proj, [3, 97])
cols = rgb[inside]


def mean_hex(sel):
    c = (cols[sel].mean(0) * 255).round().astype(int)
    return "#%02X%02X%02X" % tuple(c)


stops = []
for q in np.linspace(0, 1, 5):
    centre_p = lo + q * (hi - lo)
    sel = np.abs(proj - centre_p) < (hi - lo) * 0.06
    stops.append({"offset": float(q), "colour": mean_hex(sel)})

params = {
    "size": [int(rgb.shape[1]), int(rgb.shape[0])],
    "ring_outer": fit(ring_outer),
    "ring_inner": fit(ring_inner),
    "gradient": {
        "from": (direction * lo).tolist(),
        "to": (direction * hi).tolist(),
        "stops": stops,
    },
}
rc = (np.median(rgb[ring & coloured], 0) * 255).round().astype(int)
params["ring_colour"] = "#%02X%02X%02X" % tuple(rc)
redc = (rgb[red].mean(0) * 255).round().astype(int)
params["red_colour"] = "#%02X%02X%02X" % tuple(redc)
gc = (rgb[grey].mean(0) * 255).round().astype(int)
params["grey_colour"] = "#%02X%02X%02X" % tuple(gc)

# Tight body: just the painted pixels, with the scales and eye filled in.
body_paint = paint_nr & body
body = ndi.binary_fill_holes(ndi.binary_closing(body_paint, disk(2)))
body_white = white & body & ~body_paint

# The bib: the grey-edged blade at the lower left, below and left of the body.
not_ring = ~ndi.binary_dilation(ring, disk(3))
ys_, xs_ = np.mgrid[0:paint.shape[0], 0:paint.shape[1]]
bib_box = (xs_ < 0.47 * paint.shape[1]) & (ys_ > 0.36 * paint.shape[0]) & (ys_ < 0.82 * paint.shape[0])
bib_edge = (grey | black) & bib_box & not_ring & ~body
bib = ndi.binary_fill_holes(ndi.binary_closing(bib_edge, disk(4)))
lab, n = ndi.label(bib)
sizes = ndi.sum(bib, lab, range(1, n + 1))
bib = lab == (1 + int(np.argmax(sizes)))
# Body seen through the clear bib, at the mouth.
light = (sat > 0.08) & (mx > 0.6) & ~white & ~red
mouth = light & ~body & not_ring & ndi.binary_dilation(bib, disk(6)) & ~ndi.binary_erosion(bib, disk(30))
mouth = ndi.binary_opening(mouth, disk(2))
lab, n = ndi.label(mouth)
if n:
    sizes = ndi.sum(mouth, lab, range(1, n + 1))
    mouth = np.isin(lab, 1 + np.where(sizes > 150)[0])
mc = (rgb[mouth].mean(0) * 255).round().astype(int) if mouth.any() else np.array([220, 160, 200])
params["mouth_colour"] = "#%02X%02X%02X" % tuple(mc)

# The eye's white, its pupil and the dot on the back are near-perfect ellipses
# in the original artwork; fit them rather than trace them.
ellipses = []
lab, n = ndi.label(red)
for k in range(1, n + 1):
    comp = lab == k
    if comp.sum() < 100:
        continue
    pts = np.stack(np.nonzero(comp)[::-1], 1)
    cnt = cv2.findContours(comp.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0]
    ellipses.append({"layer": "red", **fit(cv2.fitEllipse(cnt.astype(np.float32)))})
    # an eye if white surrounds it
    ring_zone = ndi.binary_dilation(comp, disk(12)) & ~ndi.binary_dilation(comp, disk(2))
    if (body_white & ring_zone).mean() > 0.3 * ring_zone.mean():
        eye = ndi.binary_fill_holes(ndi.binary_closing((body_white | comp) & ndi.binary_dilation(comp, disk(40)), disk(3)))
        lab2, n2 = ndi.label(eye)
        eye = lab2 == lab2[tuple(pts.mean(0).astype(int)[::-1])]
        cnt = cv2.findContours(eye.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0]
        ellipses.insert(0, {"layer": "body_white", **fit(cv2.fitEllipse(cnt.astype(np.float32)))})
        body_white = body_white & ~ndi.binary_dilation(eye, disk(2))
params["ellipses"] = ellipses

# Each layer: a binary mask saying where it is, and optionally a continuous
# "how much" map whose upscaled 0.5 contour gives a smoother edge than the
# aliased binary mask would.
redness = np.clip((r - np.maximum(g, b)) / 0.7, 0, 1)
darkness = np.clip((1 - mx) / 0.8, 0, 1)
whiteness = np.clip((mn - 0.55) / 0.4, 0, 1)
paintness = np.clip(sat / 0.3, 0, 1)
layers = {
    "ring": (ring, None),
    "bib": (bib, None),
    "body": (body, paintness),
    "mouth": (mouth, None),
    "body_white": (body_white, whiteness),
    "grey": (grey & not_ring & ~body, None),
    "black": (black, darkness),
}


def upscale(a):
    return cv2.resize(a.astype(np.float32), None, fx=UPSCALE, fy=UPSCALE, interpolation=cv2.INTER_CUBIC)


def save(name, m, soft):
    cv2.imwrite(f"{outdir}/{name}.png", np.where(m, 0, 255).astype(np.uint8))
    if soft is None:
        big = cv2.GaussianBlur(upscale(m), (0, 0), UPSCALE * SMOOTH) > 0.5
    else:
        near = upscale(ndi.binary_dilation(m, disk(2))) > 0.5
        big = (cv2.GaussianBlur(upscale(soft), (0, 0), UPSCALE * SMOOTH) > 0.5) & near
        if name == "body":
            big = ndi.binary_fill_holes(big)
    cv2.imwrite(f"{outdir}/{name}.pbm", np.where(big, 0, 255).astype(np.uint8))


for name, (m, soft) in layers.items():
    save(name, m, soft)

with open(f"{outdir}/params.json", "w") as f:
    json.dump(params, f, indent=2)
print(json.dumps(params, indent=2))
