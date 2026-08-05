# Changelog

## v0.0.3

- Cards now pack edge-to-edge and flush to the top of the sheet (no outer
  margins, no gaps), so the sheet's own trim edges are the outer borders. Cut
  marks reduced to only what's needed: two full-height vertical cuts between the
  cards (a single cut splits the shared white into an even ~3.7 mm border on
  each) and one bottom trim line — nothing to cut on the left, right, or top.

## v0.0.2

- Photos are now composited inside a full **instax-mini card** (54×86 mm) with
  the real white border — thin top/sides, thick bottom — so print-and-cut
  results look like actual instax minis. Cut marks moved to the card corners,
  now light-grey trim lines plus black corner crosses.

## v0.0.1 — initial

- Three interactive instax-mini crop stations (drag to move, wheel to zoom,
  90° buttons + angle slider to rotate); frame locked to the 46×62 mm instax
  ratio and constrained to stay inside the image.
- Live effective-DPI readout per crop with a low-resolution warning.
- 4R (15×10 cm) sheet generation: three photos across the width at ~instax
  size, centred, with cut-mark crosses at every corner.
- Preview dialog with Save (300-DPI JPEG/PNG/TIFF, physical size embedded) and
  direct Print.
