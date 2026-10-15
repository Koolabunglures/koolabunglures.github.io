#!/bin/bash
# Rebuild the boat logo print files from the source bitmaps.
#
# Needs: potrace, rsvg-convert (librsvg), gs (ghostscript), qpdf, and a Python
# with numpy, scipy, opencv-python-headless and pillow, given as $PYTHON.
#
# Writes to logo/boat/:
#   koolabung-lures-boat[-outline].svg   vector master, RGB
#   koolabung-lures-boat[-outline].pdf   vector, CMYK — send this to the printer
#   koolabung-lures-boat[-outline].eps   vector, CMYK — for printers who ask for EPS
#   koolabung-lures-boat[-outline].png   transparent preview, 150 dpi at 1 m wide
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON=${PYTHON:-python3}
WIDTH_MM=1000
LURE_SCALE=0.9

mkdir -p build/layers boat
"$PYTHON" -I tools/separate.py source/lure-swoosh.bmp build/layers >/dev/null
"$PYTHON" -I tools/build_lure.py build/layers build/lure.svg
"$PYTHON" -I tools/trace_wordmark.py source/wordmark.bmp build/wordmark.json >/dev/null

for variant in "" "-outline"; do
  name=boat/koolabung-lures-boat$variant
  flag=${variant:+--outline}
  "$PYTHON" -I tools/compose.py build/wordmark.json build/lure.svg "$name.svg" \
    --lure-scale "$LURE_SCALE" --align right --width-mm "$WIDTH_MM" $flag
  rsvg-convert -f pdf "$name.svg" -o "build/rgb.pdf"
  # Not gs's own CMYK conversion: it rasterises the gradient.
  "$PYTHON" -I tools/cmyk_pdf.py build/rgb.pdf "$name.pdf" >/dev/null
  gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=eps2write -o "$name.eps" "$name.pdf"
  rsvg-convert --dpi-x 150 --dpi-y 150 "$name.svg" -o "$name.png"
done
ls -la boat
