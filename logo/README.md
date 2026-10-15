# Logo

Vector rebuild of the Koolabung Lures lure-and-swoosh logo, laid out for the
side of the boat.

## Print files (`boat/`)

Send the whole folder. `koolabung-lures-printer-brief.pdf` tells the printer
which file suits which hull colour and gives the specs and colour values.

| File | Use |
|---|---|
| `koolabung-lures-boat.pdf` | Full colour, 1000 mm wide nominal. White and light hulls. |
| `koolabung-lures-boat-outline.pdf` | Same, with a white outline and white inside the swoosh. Aluminium and dark hulls. |
| `koolabung-lures-boat-outline-cut.pdf` | Outline version plus a contour cut line in the `CutContour` spot colour, for print-and-cut. |
| `one-colour/` | Purple, white and black single-colour versions for plotter-cut vinyl. |
| `parts/` | Lure and wordmark on their own, plain and outlined, at the scale they have in the full logo. |

Each PDF is vector CMYK, with matching `.eps`, an RGB `.svg` master and a
`.png` preview. White areas carry no ink; they rely on white vinyl.

## Rebuilding

`tools/build.sh` regenerates everything from `source/`:

- `source/lure-swoosh.bmp`: the lure and swoosh. Split into colour layers
  (`separate.py`), traced with potrace and reassembled with the swoosh as two
  fitted ellipses and the body as a gradient (`build_lure.py`).
- `source/wordmark.bmp`: "Koolabung / Lures", traced line by line
  (`trace_wordmark.py`).
- `compose.py` lays them out; `cmyk_pdf.py` converts the PDF to CMYK without
  rasterising the gradient, which Ghostscript's own conversion does, and turns
  the cut line into the `CutContour` spot colour.
- `trace_shape.py` renders a composed logo and traces it again for the
  one-colour versions and the cut line.
- `brief.py` writes the printer brief.

```
PYTHON=/path/to/python tools/build.sh   # python with numpy scipy opencv-python-headless pillow
```

Also needs `potrace`, `rsvg-convert` (librsvg), `gs` and `qpdf`.
