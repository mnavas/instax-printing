# Changelog

## v0.0.8

- **Instax-inspired visual refresh.** New light, warm palette with the signature
  **instax pink** as the accent (buttons, crop frames, sliders, menu highlights)
  and photos on dark canvases for contrast. The whole palette lives in one place
  (`ui_common`) and a single global stylesheet styles the common widgets.
- **The checkboxes are now clearly visible** — a white box that fills **pink** when
  checked (the old dark-on-dark checkbox was almost invisible). Combos, sliders,
  menus and tooltips got the same consistent treatment.

## v0.0.7

- **Collages no longer add an outer border.** Photos now fill the instax image
  area edge-to-edge, because the instax film already supplies the physical white
  border — the old version added its own, which doubled up when printed on an
  instax printer.
- **Gutter between photos is thin and selectable** — **None / Thin / Medium**
  (default Thin), instead of a fixed 2 mm margin on every side. It's chosen in the
  **export preview**, so you can see it and adjust before printing.
- **More layouts** (15 total), including asymmetric ones: `1`, `2` (side-by-side
  / stacked), `3` (columns / rows / 1 top + 2 / 1 bottom + 2 / 1 left + 2 / 1
  right + 2), `4` (2×2 / columns / rows), `5` (1 top + 4), `6` (3×2), `9` (3×3).
  The "1 + 2" styles come in all four orientations (big on top / bottom / left /
  right).
- The **crop-station grid now mirrors the chosen layout** (correct cell sizes,
  spans, and orientation).
- **Changing the Format, Layout, or Gutter no longer clears your photos.** The
  crop stations are reused, so loaded photos (and their framing) survive the
  change — only cells that a smaller layout removes are dropped.
- **The gutter and the border are both chosen in the export preview**, which
  updates live so you can see how it looks and decide before printing. The border
  is a simple toggle: **off** = image only (for an instax printer — the film adds
  the white border; default), **on** = the full white instax card border (for a
  normal printer).
- Also shown on empty crop slots: the instax target frame, so orientation is
  obvious before loading (portrait for Mini, landscape for Wide).

## v0.0.6

- **Main menu** added. A **Tools** menu switches between the two tools; **File →
  Quit** closes the app.
- **Instax Collage** tool (new). Pick an instax **format** — Mini (46×62 mm),
  Square (62×62 mm), or Wide (99×62 mm) — and a preset **grid layout** (1, 2, 3,
  or 2×2), then fill each cell with a pan/zoom/rotate crop.
  - **Export as a plain image** sized to the instax printer's native resolution
    (the printer adds the physical border), **or with the white instax border**
    drawn on — toggled in the preview.
  - Saves with the instax print DPI embedded, reusing the last-used folder and
    incremental naming.
- Internals: `CropCanvas` is now output-size agnostic (any aspect ratio), and the
  crop station, save/print, and styles are shared between both tools.

## v0.0.5

- **New sheet** button clears all three photos to start over (with a
  confirmation prompt when photos are loaded).
- **Save** now opens in the folder used last (this session) instead of always
  defaulting to a fixed name.
- **Save** suggests an incremental name (`instax_4r`, `instax_4r_1`,
  `instax_4r_2`, …), so saving successive sheets never overwrites a previous one.

## v0.0.4

- Added a project **landing page** (`index.html`) and full **docs**
  (`docs/installation.md`, `docs/user-guide.md`, `docs/architecture.md`).
- Added a **Support the project** section (GitHub Sponsors, PayPal, and a
  **De Una · Banco Pichincha** QR — `assets/deuna-qr.png`) on the landing page
  and in the README.

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
