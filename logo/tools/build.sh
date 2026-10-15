#!/bin/bash
# Rebuild the boat logo print files from the source bitmaps.
#
# Needs: potrace, rsvg-convert (librsvg), gs (ghostscript), qpdf, and a Python
# with numpy, scipy, opencv-python-headless and pillow, given as $PYTHON.
#
# Writes to logo/boat/ (see README.md for what each file is for). Every
# artwork gets .svg (RGB vector master), .pdf (vector, CMYK), .eps (vector,
# CMYK) and .png (transparent preview, 150 dpi at its print size).
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON=${PYTHON:-python3}
WIDTH_MM=1000
LURE_SCALE=0.9
NAME=koolabung-lures

mkdir -p build/layers boat/one-colour boat/parts
"$PYTHON" -I tools/separate.py source/lure-swoosh.bmp build/layers >/dev/null
"$PYTHON" -I tools/build_lure.py build/layers build/lure.svg
"$PYTHON" -I tools/trace_wordmark.py source/wordmark.bmp build/wordmark.json >/dev/null

compose() {  # <out.svg> [compose.py flags]
  local out=$1; shift
  "$PYTHON" -I tools/compose.py build/wordmark.json build/lure.svg "$out" \
    --lure-scale "$LURE_SCALE" --align right --width-mm "$WIDTH_MM" "$@" >/dev/null
}

# svg -> pdf, eps, png alongside it
outputs() {  # <path/without/extension> [--no-png]
  local name=$1
  rsvg-convert -f pdf "$name.svg" -o build/rgb.pdf
  # Not gs's own CMYK conversion: it rasterises the gradient.
  "$PYTHON" -I tools/cmyk_pdf.py build/rgb.pdf "$name.pdf" >"build/$(basename "$name").colours"
  gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=eps2write -o "$name.eps" "$name.pdf"
  [ "${2:-}" = --no-png ] || rsvg-convert --dpi-x 150 --dpi-y 150 "$name.svg" -o "$name.png"
}

# Full colour, whole logo
compose "boat/$NAME-boat.svg"
compose "boat/$NAME-boat-outline.svg" --outline
"$PYTHON" -I tools/trace_shape.py cut-contour "boat/$NAME-boat-outline.svg" "boat/$NAME-boat-outline-cut.svg"
for v in boat boat-outline; do outputs "boat/$NAME-$v"; done
outputs "boat/$NAME-boat-outline-cut" --no-png

# One colour, for plotter-cut vinyl
for c in purple:#64348A white:#FFFFFF black:#000000; do
  out="boat/one-colour/$NAME-boat-${c%%:*}"
  "$PYTHON" -I tools/trace_shape.py one-colour "boat/$NAME-boat.svg" "$out.svg" --fill "${c#*:}"
  outputs "$out"
done

# Lure and wordmark on their own, at the size they are in the whole logo
for part in lure:lure wordmark:text; do
  out="boat/parts/$NAME-${part%%:*}"
  compose "$out.svg" --parts "${part#*:}"
  compose "$out-outline.svg" --parts "${part#*:}" --outline
  outputs "$out"
  outputs "$out-outline"
done

"$PYTHON" -I tools/brief.py boat "build/$NAME-boat.colours" build/brief
rsvg-convert -f pdf build/brief-1.svg build/brief-2.svg -o "boat/$NAME-printer-brief.pdf"
find boat -type f -not -path '*/.claude/*' | sort
