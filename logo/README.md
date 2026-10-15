# Logo

Vector rebuild of the Koolabung Lures lure-and-swoosh logo, laid out for the
side of the boat.

## Print files (`boat/`)

| File | Use |
|---|---|
| `koolabung-lures-boat.pdf` | Send to the printer. Vector, CMYK, 1000 mm wide nominal. |
| `koolabung-lures-boat-outline.pdf` | Same, with a white outline and white inside the swoosh, for a dark hull. |
| `*.eps` | Same artwork, for printers who ask for EPS. |
| `*.svg` | RGB vector masters. |
| `*.png` | Transparent previews, 150 dpi at 1 m wide. |

White areas carry no ink; they rely on white vinyl.

## Rebuilding

`tools/build.sh` regenerates everything from `source/`:

- `source/lure-swoosh.bmp`: the lure and swoosh. Split into colour layers
  (`separate.py`), traced with potrace and reassembled with the swoosh as two
  fitted ellipses and the body as a gradient (`build_lure.py`).
- `source/wordmark.bmp`: "Koolabung / Lures", traced line by line
  (`trace_wordmark.py`).
- `compose.py` lays them out; `cmyk_pdf.py` converts the PDF to CMYK without
  rasterising the gradient, which Ghostscript's own conversion does.

```
PYTHON=/path/to/python tools/build.sh   # python with numpy scipy opencv-python-headless pillow
```

Also needs `potrace`, `rsvg-convert` (librsvg), `gs` and `qpdf`.
