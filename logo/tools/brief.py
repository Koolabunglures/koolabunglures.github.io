"""Write the printer brief: which file to use for which hull, and the specs.

Usage: python brief.py <boatdir> <colours.txt> <out-prefix>
Writes <out-prefix>-1.svg and <out-prefix>-2.svg (A4 landscape, mm units),
for rsvg-convert to join into one PDF.

<colours.txt> is cmyk_pdf.py's output for the full-colour logo.
"""
import re
import sys
from html import escape

boat, colours_file, prefix = sys.argv[1:4]
NAME = "koolabung-lures"
FONT = 'font-family="Helvetica, Arial, sans-serif"'
INK = "#222222"
MUTED = "#666666"
HULLS = [  # name, colour, recommended file
    ("White / cream", "#F2F1EC", "standard"),
    ("Bare aluminium", "#A7ACB0", "outline"),
    ("Navy / dark blue", "#1D2B45", "outline"),
    ("Black / dark grey", "#1A1A1A", "outline"),
]


def logo(path):
    """Inline a logo SVG as a nested <svg>, keeping its viewBox."""
    src = open(path).read()
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    body = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    return vb, body


def size_mm(path):
    w, h = re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"', open(path).read()).groups()
    return f"{float(w):.0f} × {float(h):.0f} mm"


def place(path, x, y, w, h):
    vb, body = logo(path)
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}">{body}</svg>'


def text(x, y, s, size=3.6, weight="normal", fill=INK, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" {FONT}>{escape(s)}</text>')


def page(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="297mm" height="210mm" viewBox="0 0 297 210">'
            f'<rect width="297" height="210" fill="#FFFFFF"/>{body}</svg>\n')


# Page 1: which version for which hull
p1 = [
    text(15, 20, "Koolabung Lures: boat decal artwork", 7, "bold"),
    text(15, 28, "Which version to use. Choose the column marked for the hull colour.", 4, fill=MUTED),
    text(70, 42, "Standard", 4, "bold", anchor="middle"),
    text(70, 47, f"{NAME}-boat.pdf", 3, fill=MUTED, anchor="middle"),
    text(200, 42, "White outline", 4, "bold", anchor="middle"),
    text(200, 47, f"{NAME}-boat-outline.pdf", 3, fill=MUTED, anchor="middle"),
]
for i, (hull, colour, pick) in enumerate(HULLS):
    y = 54 + i * 37
    p1.append(text(15, y + 17, hull, 3.8, "bold"))
    for col, (variant, cx) in enumerate([("standard", 70), ("outline", 200)]):
        x = cx - 62
        chosen = variant == pick
        p1.append(f'<rect x="{x}" y="{y}" width="124" height="33" rx="1.5" fill="{colour}" '
                  f'stroke="{"#2E9E4F" if chosen else "#CCCCCC"}" stroke-width="{1.2 if chosen else 0.3}"/>')
        f = f"{boat}/{NAME}-boat{'-outline' if variant == 'outline' else ''}.svg"
        p1.append(place(f, x + 8, y + 3, 108, 27))
    p1.append(text(266, y + 18, "✓ " + ("Standard" if pick == "standard" else "Outline"), 3.8, "bold",
                   fill="#2E9E4F"))
p1.append(text(15, 203, "Other hull colours: if purple text on the hull is hard to read from 20 m, use the outline.",
               3.2, fill=MUTED))

# Page 2: files and specs
rows = [
    ("Main files", None),
    (f"{NAME}-boat.pdf", "Full colour. White and light hulls."),
    (f"{NAME}-boat-outline.pdf", "Full colour with white outline. Aluminium and dark hulls."),
    (f"{NAME}-boat-outline-cut.pdf", "Outline version plus contour cut line: spot colour CutContour, 0.1 mm, overprint."),
    ("*.eps", "Same artwork as each PDF, for software that wants EPS."),
    ("*.svg", "RGB vector masters."),
    ("*.png", "Previews only. Not for print."),
    ("one-colour/", None),
    (f"{NAME}-boat-purple / -white / -black", "Single colour, for plotter-cut vinyl. Lure detail is simplified;"),
    ("", "the colour gradient on the lure can only be reproduced by printing."),
    ("parts/", None),
    (f"{NAME}-lure[-outline]", "Lure and swoosh on their own, at the same scale as in the full logo."),
    (f"{NAME}-wordmark[-outline]", "\"Koolabung Lures\" text on its own, same scale."),
]
p2 = [text(15, 20, "Files and specifications", 7, "bold")]
y = 32
for name, desc in rows:
    if desc is None:
        y += 2
        p2.append(text(15, y, name, 4, "bold"))
    else:
        p2.append(text(19, y, name, 3.2, "bold" if name.endswith(".pdf") else "normal"))
        p2.append(text(105, y, desc, 3.2))
    y += 5.6

specs = [
    ("Size", f"{size_mm(f'{boat}/{NAME}-boat.svg')} (outline version {size_mm(f'{boat}/{NAME}-boat-outline.svg')}). "
             "Vector: scale to fit the hull, keep proportions."),
    ("Quantity", "2: one each side of the boat. Same artwork both sides. Do not mirror."),
    ("Material", "Print on white marine-grade cast vinyl with UV laminate. Contour cut."),
    ("White", "No white ink. White areas are the vinyl showing through."),
    ("Colour", "CMYK, converted with Generic CMYK, relative colorimetric. RGB values below for matching."),
]
y += 4
p2.append(text(15, y, "Specifications", 4, "bold"))
y += 6
for k, v in specs:
    p2.append(text(19, y, k, 3.2, "bold"))
    p2.append(text(45, y, v, 3.2))
    y += 5.6

y += 4
p2.append(text(15, y, "Colours", 4, "bold"))
y += 4
roles = {"#64348A": "Text", "#4C368B": "Swoosh", "#C4020A": "Eye", "#BC7CB0": "Mouth",
         "#CBCACC": "Grey", "#18171A": "Black", "#FFFFFF": "White (no ink)"}
for i, line in enumerate(l for l in open(colours_file).read().splitlines() if l.strip()):
    rgb, cmyk = line.split(" -> CMYK ")
    cx, cy = 19 + (i % 3) * 90, y + (i // 3) * 8
    p2.append(f'<rect x="{cx}" y="{cy}" width="6" height="6" fill="{rgb}" stroke="#CCCCCC" stroke-width="0.2"/>')
    p2.append(text(cx + 8, cy + 4.2, roles.get(rgb, "Lure body gradient"), 3.2, "bold"))
    p2.append(text(cx + 42, cy + 4.2, f"{rgb}  CMYK {'/'.join(cmyk.split())}", 3.2))

for n, body in [(1, p1), (2, p2)]:
    open(f"{prefix}-{n}.svg", "w").write(page("".join(body)))
