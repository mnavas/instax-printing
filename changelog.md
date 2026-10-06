# Changelog

## v0.0.13

- **Layout selector in the main 4R window.** A new **Layout** dropdown at the top
  of the 4R Print Sheet tool chooses the sheet arrangement up front (it used to be
  buried as a border toggle inside the preview dialog):
  - **3 × Instax mini — white frame** (the classic look)
  - **4 × Instax mini — no frame (portrait)** — the sheet turns portrait so four
    full-size upright minis fit as a 2×2 (where only three fit on a landscape sheet)
  - **2 × 2 grid — 4 photos**
  - **3 × 2 grid — 6 photos**
  - **2 × 3 grid — 6 photos**
  The grid layouts separate the photos with white gutters and draw cut lines down
  their middle, so you print, then cut, into bordered prints. The crop stations now
  rebuild to match the chosen layout (correct number of photos, each cropped to the
  right aspect) and are arranged to mirror the printed grid.
- **Preview dialog always fits the screen.** The preview is now bounded to the
  available screen height (not just a fixed width), so tall/portrait sheets no
  longer push the Save / Print buttons off-screen.

## v0.0.12

- **High-resolution saving (600 DPI) in every tool.** A **High resolution
  (2× · 600 DPI)** checkbox in each preview re-renders the output at double the
  pixels and double the DPI — sampled from the **source photos**, so the extra
  pixels are real detail, not upscaling. Works for the 4R sheet (both border
  styles), the instax collage (image or bordered), and the A4 sheet. Leave it off
  for the usual 300-DPI output.

## v0.0.11

- **4R sheet: choose the border in the preview.** The 4R Print Sheet now offers
  two styles, picked live in the preview:
  - **Instax border** (default) — each photo in a full instax card (white frame,
    thick bottom), as before.
  - **Thin border only** — each photo with just a thin uniform white border, so
    the images print **bigger**, with cut lines to trim them out.

## v0.0.10

- **Corrected the instax border dimensions.** The top border is **8 mm** (not
  4 mm), making the bottom border **16 mm** — matching a real instax print. All
  three formats share the same 86 mm frame / 62 mm image, so they all use 8 mm
  top / 16 mm bottom; only the side border differs (Mini 4 mm, Square 5 mm, Wide
  4.5 mm). Fixes the white-bordered output of every tool (4R sheet, collage with
  border, and the A4 sheet).

## v0.0.9

- **New tool: A4 Instax Sheet** (Tools → A4 Instax Sheet). Packs the **maximum
  instax cards onto a landscape A4** for home printing — **10** Mini (5×2), **8**
  Square (4×2), or **4** Wide (2×2). Fill as many cards as you like (partial OK),
  then generate a print-ready A4:
  - **True-size** instax cards (300 DPI) with the full white border — not reduced.
  - A **cut line** around each card (edge-to-edge, so one cut serves two).
  - The block is **centred inside a small margin**, so it prints centred on A4
    without edge-clipping.
  - Save a 300-DPI A4 image, or Print.

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
