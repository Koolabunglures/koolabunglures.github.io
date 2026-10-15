"""Convert cairo's RGB vector PDF to CMYK without rasterising anything.

Usage: python cmyk_pdf.py <in.pdf> <out.pdf>
Needs qpdf (with fix-qdf) on PATH, and Pillow.

Ghostscript's CMYK conversion turns the lure's gradient into a low-resolution
bitmap. The logo uses only flat fills and one axial gradient, so instead this
rewrites each RGB colour in place: "r g b rg/RG" operators, the gradient's
C0/C1 stops, and DeviceRGB colour spaces. Colours go through macOS's Generic
CMYK profile with relative colorimetric intent.
"""
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageCms

PROFILE = "/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc"

src, out = sys.argv[1], sys.argv[2]
to_cmyk = ImageCms.buildTransform(
    ImageCms.createProfile("sRGB"), ImageCms.getOpenProfile(PROFILE), "RGB", "CMYK",
    renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
)
cache = {}


def cmyk(r, g, b):
    key = tuple(round(float(v) * 255) for v in (r, g, b))
    if key not in cache:
        px = ImageCms.applyTransform(Image.new("RGB", (1, 1), key), to_cmyk).getpixel((0, 0))
        cache[key] = " ".join(f"{v / 255:.4f}" for v in px)
    return cache[key]


NUM = r"(-?\d*\.?\d+)"
with tempfile.TemporaryDirectory() as tmp:
    qdf = f"{tmp}/in.qdf"
    subprocess.run(["qpdf", "--qdf", "--object-streams=disable", src, qdf], check=True)
    text = open(qdf, "rb").read().decode("latin-1")

    text = re.sub(rf"(?<![\w.]){NUM} {NUM} {NUM} rg\b", lambda m: f"{cmyk(*m.groups())} k", text)
    text = re.sub(rf"(?<![\w.]){NUM} {NUM} {NUM} RG\b", lambda m: f"{cmyk(*m.groups())} K", text)
    text = re.sub(
        rf"/(C0|C1) \[\s*{NUM}\s+{NUM}\s+{NUM}\s*\]",
        lambda m: f"/{m.group(1)} [ {cmyk(*m.groups()[1:])} ]", text,
    )
    text = text.replace("/DeviceRGB", "/DeviceCMYK")

    fixed = f"{tmp}/fixed.qdf"
    open(f"{tmp}/edited.qdf", "wb").write(text.encode("latin-1"))
    with open(fixed, "wb") as f:
        subprocess.run(["fix-qdf", f"{tmp}/edited.qdf"], check=True, stdout=f)
    subprocess.run(["qpdf", "--compress-streams=y", "--object-streams=generate", fixed, out], check=True)

for rgb, c in sorted(cache.items()):
    print("#%02X%02X%02X" % rgb, "-> CMYK", " ".join(f"{float(v) * 100:.0f}" for v in c.split()))
