# instax-printing — Architecture & Developer Guide

## Overview

instax-printing is a small, single-window PyQt6 app. The design keeps the
**geometry maths and image processing decoupled from Qt**: everything about
physical sizes lives in `instax_config.py`, the crop-transform and I/O maths live
in `imaging.py`, and the 4R assembly lives in `composite.py` — all three are pure
functions over NumPy arrays with no Qt imports. Only `crop_canvas.py` and
`main_window.py` touch Qt.

That split means the crop and compositing logic can be unit-tested (or scripted)
without a running UI.

---

## Module Map

```
instax-printing/
├── main.py            Entry point — boots Qt (Fusion style), shows MainWindow
├── instax_config.py   Physical sizes (mm) → px, the 3-up layout, instax formats + collage layouts
├── imaging.py         Unicode-safe image I/O, incremental naming + the crop-transform maths (no Qt)
├── composite.py       Assembles the 4R sheet and draws the cut marks (no Qt)
├── collage.py         Assembles an instax-format collage, image-only or bordered (no Qt)
├── a4_sheet.py        Packs the max instax cards onto a landscape A4 with cut lines (no Qt)
├── crop_canvas.py     CropCanvas widget — interactive move/zoom/rotate frame (any output size)
├── crop_station.py    CropSlot widget — a CropCanvas + load/rotate/reset + sliders + DPI hint
├── ui_common.py       Palette + global style, button styles + save/print helpers
├── collage_page.py    CollagePage + CollagePreviewDialog — the collage tool UI
├── a4_page.py         A4Page — the A4 Instax Sheet tool UI
├── main_window.py     SheetPage, PreviewDialog, MainWindow (menu + page stack)
├── run.sh             venv bootstrap + launcher
└── requirements.txt   PyQt6, opencv-python, Pillow, numpy
```

**Dependency direction:** `main_window` → (`collage_page`, `crop_station`,
`composite`, `ui_common`, `instax_config`); `collage_page` → (`collage`,
`crop_station`, `ui_common`, `instax_config`); `crop_station` → (`crop_canvas`,
`ui_common`, `instax_config`); `crop_canvas`/`composite`/`collage` →
(`imaging`, `instax_config`); `ui_common` → `imaging`; `imaging` → (nothing
project-local). Nothing lower ever imports upward.

The pure-NumPy layer (`imaging`, `composite`, `collage`, `instax_config`) stays
free of Qt; the widget layer (`crop_canvas`, `crop_station`, `collage_page`,
`main_window`) and `ui_common` are the only Qt-aware modules.

---

## Three Tools, One Window

`MainWindow` is a `QMainWindow` with a menu bar and a `QStackedWidget` holding
three pages:

- **`SheetPage`** (index 0) — the original 4R tool: three `CropSlot`s locked to
  the instax-mini output size, a status line, **New sheet** / **Generate 4R
  sheet** buttons, and `PreviewDialog` for save/print.
- **`CollagePage`** (index 1) — the collage tool (see below).
- **`A4Page`** (index 2) — the A4 tool (see below).

The **Tools** menu holds three checkable, mutually exclusive actions (a
`QActionGroup`) that call `_show_page(index)`; **File → Quit** closes the window.
`PreviewDialog` is shared by the 4R and A4 tools (its `title` / `base_name` / `dpi`
are parameters); `A4Page` receives a small factory so it can open one without
importing `main_window` (avoiding a cycle).

---

## The Coordinate / Size Model

Everything is anchored to **real millimetres** and rasterised at
`PRINT_DPI = 300`, so the exported file has correct physical proportions.

| Thing | mm | px @ 300 DPI | Constant(s) |
|-------|-----|--------------|-------------|
| 4R sheet (landscape) | 152.4 × 101.6 | 1800 × 1200 | `CANVAS_W`, `CANVAS_H` |
| instax card | 54 × 86 | 638 × 1016 | `CARD_W`, `CARD_H` |
| instax image area | 46 × 62 | 543 × 732 | `INSTAX_W`, `INSTAX_H` |
| side border | 4 | ~47 | — |
| top border | 8 | ~94 | `TOP_BORDER_PX` |

`mm_to_px(mm)` is the single conversion used everywhere. The image area sits
inside the card centred horizontally, with 4 mm side borders and an 8 mm top
border; the bottom border is whatever's left (**16 mm**) — the classic instax
look (image offset toward the top, thicker bottom).

### Layout functions (`instax_config.py`)

- `image_offset()` → `(x, y)` top-left of the image area inside a native card.
- `card_print_size()` → `(w, h)` printed size of each card so three fit across
  the 4R width, **capped at native size** so cards are never upscaled.
- `card_positions()` → the three `(x, y)` top-lefts on the canvas — packed
  edge-to-edge (`GAP_MM = 0`) and flush to the top/left (`MARGIN_MM = 0`), so the
  three cards fill the full width and the sheet's own edges are the outer borders.

---

## The Crop Model (`imaging.py`)

The output is a fixed instax-ratio rectangle (`INSTAX_W × INSTAX_H`). The user
positions an instax-shaped frame over the source by **moving** it (`cx, cy` in
source pixels), **scaling** it (`scale`), and **rotating** it (`angle`, degrees):

```
p_out = scale · R(angle) · (p_src − c) + o        (c = (cx, cy), o = output centre)
```

A **larger `scale` means a smaller frame in source space** — a tighter, more
zoomed-in crop.

Key functions:

| Function | Purpose |
|----------|---------|
| `imread(path)` | Unicode-safe read via `np.fromfile` + `cv2.imdecode` → BGR uint8 |
| `imwrite_print(path, img, dpi)` | Save via Pillow with DPI metadata embedded |
| `min_scale(angle, out_w, out_h, img_w, img_h)` | Smallest scale at which the **rotated** frame still fits inside the image |
| `clamp_center(cx, cy, …)` | Clamps the frame centre so the rotated frame stays inside the image (no blank edges) |
| `crop_matrix(…)` | 2×3 affine (source → output) for `cv2.warpAffine` |
| `render_crop(img, …)` | Produces the final `out_w × out_h` BGR crop |
| `crop_quad_src(…)` | The four output-rect corners **in source pixels**, for the on-screen overlay |

`min_scale` + `clamp_center` are what guarantee the crop can never contain blank
borders: the frame's minimum size is derived from its rotated bounding box, and
its centre is clamped to the region where that box fits.

---

## The Interactive Crop (`crop_canvas.py`)

`CropCanvas` is a `QWidget` that renders the whole source image fit-to-widget and
draws the instax frame as a polygon on top (with the outside dimmed and a
rule-of-thirds grid inside). It emits a `changed` signal whenever the frame moves.

State:

- `angle` — degrees, wrapped to `(−180, 180]`.
- `zoom` — `≥ 1.0`, multiplies the `min_scale` ("fills the image") baseline, up to
  `_MAX_ZOOM = 8.0`.
- `cx, cy` — frame centre in source pixels.

`scale()` returns `min_scale(angle, …) · zoom`, so `zoom = 1.0` always means "the
frame is as large as it can be at this angle" and larger values crop tighter.

Interaction:

- `wheelEvent` → smooth zoom (`1.0015 ** angleDelta`).
- `mousePressEvent` / `mouseMoveEvent` / `mouseReleaseEvent` → drag the frame
  centre (movement is converted from view pixels back to source pixels via
  `_view_scale`).
- Every change funnels through `_apply()`, which re-clamps the centre and repaints.

`source_dpi()` reports the effective print resolution: the source contributes
`INSTAX_W / scale` pixels across `INSTAX_W_MM`, so
`dpi = (INSTAX_W / scale) / (INSTAX_W_MM / 25.4)`. Below ~180 the UI flags it.

`get_output()` calls `render_crop(...)` to produce the final instax-ratio image
handed to the compositor.

---

## Compositing the Sheet (`composite.py`)

```
build_4r(crops, instax_border=True, thin_border_mm=2.0)   # 3 instax-ratio crops
  ├─ instax_border → _build_4r_instax(crops)              # full instax cards
  └─ else          → _build_4r_thin(crops, thin_border_mm) # thin-bordered photos
```

Two styles, chosen in the preview:

- **`_build_4r_instax`** — `make_instax_card(crop)` builds one native-size card (a
  white `CARD_H × CARD_W` array with the crop in the `INSTAX_W × INSTAX_H` image
  area at `image_offset()`); the three cards are packed edge-to-edge, flush to the
  top. `_draw_cut_marks` draws only the cuts that layout needs — two full-height
  vertical lines at the card boundaries and one horizontal line at the card bottom
  (light grey `TRIM_LINE_COLOR`); the left/right/top edges are the sheet's own.
- **`_build_4r_thin`** — `make_thin_card(crop, border_px)` gives each photo only a
  thin uniform white border; the three are sized to fit the 4R width (capped at
  native), centred, and each gets a `cv2.rectangle` cut line. Bigger photos, no
  instax frame.

`build_4r` raises `ValueError` if it isn't given exactly three crops.

---

## Instax Formats & Collage (`instax_config.py` + `collage.py`)

### `InstaxFormat`

A frozen dataclass describing one instax size in real millimetres (image area +
full card + top/side border) plus the **native image-area pixel size of that
format's instax printer** (`print_px_w × print_px_h`). Everything else is derived:

- `dpi_x` / `dpi_y` — effective print DPI (`print_px / (img_mm / 25.4)`).
- `side_border_mm()` — `(card_w − img_w) / 2`.
- `borders_px()` — `(side, top, bottom)` border thickness in pixels; the bottom
  is the remainder `card_h − img_h − top` (the classic thick instax bottom).
- `gap_px(gap_mm)` — the white gutter width in pixels.

`INSTAX_FORMATS` holds Mini (600×800), Square (800×800), and Wide (1260×840).
`COLLAGE_LAYOUTS` holds `(label, template)` entries, where a **template** is a
list of normalised `(x, y, w, h)` cell rectangles in `0–1` that tile the frame
(a `_grid(rows, cols)` helper generates the regular ones; asymmetric layouts such
as *1 big + 4* are listed explicitly). `COLLAGE_GAP_CHOICES` (None / Thin /
Medium) and `COLLAGE_GAP_MM` set the gutter; `COLLAGE_BG` its colour.

### Building a collage

```
cell_output_sizes(fmt, template, gap_mm)          # per-cell (w, h, phys_w_mm)
build_collage(fmt, template, crops, gap_mm, with_border)
  ├─ cell_rects(template, W, H, gap)   # (x, y, w, h) per cell, filling edge-to-edge
  ├─ blit each crop into its cell      # at the printer's native resolution
  └─ with_border?  wrap the image area in a full white instax card
```

`cell_rects` tiles the image area **edge-to-edge** with a `gap` gutter only
*between* neighbours — outer edges stay flush, because the instax **film supplies
the physical border** (adding an outer margin here would double it on an instax
print). Cells may differ in size, so `cell_output_sizes` returns a size per cell.

`build_collage` returns the **bare image area** at the printer's native resolution,
or — with `with_border` — the image area wrapped in a full white instax card (for a
normal printer). It raises `ValueError` unless given exactly `len(template)` crops.
Both the `gap_mm` (gutter) and `with_border` are chosen in the export preview, so a
crop can be resized into its cell at whatever gutter the user picks without
re-framing.

---

## A4 Instax Sheet (`a4_sheet.py` + `a4_page.py`)

Packs the most instax cards that fit on a landscape A4 for home printing, at
**300 DPI physical size** (unlike the collage tool's printer-native pixels — a
cut-out A4 card must be a true-size instax).

```
A4_W_MM, A4_H_MM = 297, 210;  A4_W, A4_H = mm_to_px(...)   # 3508 x 2480
EDGE_MARGIN_MM   = 4.0                                      # block stays this far in

card_px(fmt)         -> full card (w, h) px @ 300 DPI
max_grid(fmt)        -> (cols, rows) inside A4 - 2*margin   # Mini 5x2, Square 4x2, Wide 2x2
make_card(fmt, crop) -> white card with the crop in its image area
build_a4(fmt, crops) -> A4 canvas, up to cols*rows cards, centred block + cut lines
```

`make_card` derives the card/image/border pixels from the format's millimetres
(`mm_to_px`), so Mini/Square/Wide all work. `build_a4` centres a
`cols_used × rows_used` block of edge-to-edge cards and draws a light-grey
`cv2.rectangle` cut line around each; the saved file is exactly A4 with the content
inset, so it prints centred at true size (fit-to-page or 100%).

`A4Page` is a format picker over a `QGridLayout` of `max_count(fmt)` `CropSlot`s,
reused across format changes (grow/shrink + re-size, so loaded photos survive).
**Generate A4 sheet** is enabled once ≥ 1 card is loaded; `_on_generate` passes the
filled crops to `build_a4` and opens the shared `PreviewDialog` (title / base name
`instax_a4` / 300 DPI) via the injected factory.

---

## High-resolution output (the `scale` factor)

Every compositor takes an integer `scale` (default 1); `build_4r`, `build_collage`
and `build_a4` multiply every pixel dimension by it, and `CropCanvas.get_output`
re-renders the crop at `scale`× by scaling **both** the output size and the crop
transform (so the same framed region is sampled from the source at higher
resolution — real detail, not upscaling). `ui_common.HIRES_SCALE = 2` is the one
"high resolution" step (300 → 600 DPI).

Each preview carries a **High resolution** checkbox (`ui_common.hires_checkbox()`).
The on-screen preview always renders at `scale=1`; only **Save/Print** rebuild at
`HIRES_SCALE` when it's ticked, via a `crops_fn(scale)` the page hands the dialog
(the slots re-render their crops at that scale) and embed `base_dpi × scale`. The
`PreviewDialog` used by the A4 tool takes an optional `render_fn(scale)` instead
and shows the checkbox only when one is given.

---

## The UI (`main_window.py`, `collage_page.py`, `crop_station.py`)

### `CropSlot(QWidget)` — `crop_station.py`

One crop station: a `CropCanvas` plus the **Load / ⟲ 90 / ⟳ 90 / Reset** row, the
**Zoom** and **Angle** sliders, and the DPI label. It wires the canvas's `changed`
signal to `_sync_from_canvas`, which pushes the canvas state back into the sliders
(with signals blocked to avoid feedback loops) and updates the DPI readout. The
constructor takes the crop's **output size** (and physical width for the DPI
hint), so the same widget serves instax-mini sheet slots and arbitrary-aspect
collage cells.

`_last_dir` is a **class attribute**, so the file dialog's remembered folder is
shared across every slot in both tools. `_IMG_EXTS` is listed in both cases so the
native file dialog's case-sensitive globbing doesn't hide `.JPG` photos.

### `SheetPage` / `SheetPreviewDialog` / `PreviewDialog` — `main_window.py`

`SheetPage` holds the three mini `CropSlot`s, the status line, and the **New
sheet** / **Generate 4R sheet** buttons; `_on_generate` passes the crops to
`SheetPreviewDialog`, which has a **Border** picker (**Instax border** /
**Thin border only**) that re-renders live via `composite.build_4r(...,
instax_border=...)`, plus **Save… / Print… / Close** through the shared
`ui_common` helpers. `PreviewDialog` is the simpler shared dialog (a pre-built
image + Save/Print, with `title`/`base_name`/`dpi` params) used by the A4 tool.

### `CollagePage` / `CollagePreviewDialog` — `collage_page.py`

`CollagePage` has **Format**, **Layout**, and **Gutter** combo boxes over a
`QGridLayout` of `CropSlot`s. Changing any of them calls `_rebuild_cells()`, which
**reuses** the existing `CropSlot`s (growing or shrinking the list) so loaded
photos survive a Format / Layout / Gutter change — each surviving slot is just
re-sized via `set_output_size`; only cells a smaller layout removes are dropped.
The grid **mirrors the layout**: the template's cut lines are mapped to grid
rows/columns (with `addWidget` row/column spans and proportional stretch), so a
*1 top + 4* layout shows a big station over a row of four. `_on_export` collects
the crops and opens `CollagePreviewDialog`, which sets both the **gutter** (None /
Thin / Medium) and the **instax border** (on/off) there — re-previewing live via
`collage.build_collage`, then Save/Print (DPI = the format's print DPI).

### `MainWindow(QMainWindow)` — `main_window.py`

A menu bar plus a `QStackedWidget` of `SheetPage` and `CollagePage`. The **Tools**
menu's two checkable actions switch pages; **File → Quit** closes the app.

### `ui_common.py`

Shared button styles and the `save_image` / `print_image` helpers. `save_image`
keeps a module-level last-used directory and uses `imaging.next_available_path`
for incremental names, so both tools share the behaviour.

---

## Design Notes & Rationale

- **Why a 4R sheet?** It's the cheapest, most universally available lab print
  size. Three instax cards fit on one, so you print three "instax" for the price
  of one standard photo.
- **Why cards slightly under full size?** Fitting three 54 mm cards edge-to-edge
  in 152 mm forces a ~2 mm shrink. Keeping them edge-to-edge (rather than adding
  gaps) means fewer, straighter cuts and no wasted paper.
- **Why the frame is clamped inside the image.** A print with a blank white sliver
  on one edge looks broken. Deriving the minimum scale from the rotated bounding
  box and clamping the centre makes that state unreachable, at any rotation.
- **Why DPI is surfaced live.** Instax image area is small (46 mm), so it's easy to
  over-zoom a low-res phone photo into softness without noticing. The readout (and
  the red warning) catches it before you print.
- **Why Qt is kept out of `imaging`/`composite`/`instax_config`.** Pure NumPy
  functions are testable and scriptable; the geometry can be verified without
  spinning up a window.

---

## Running in Development

```bash
cd instax-printing
source .venv/bin/activate
python main.py
```

Dependencies: `PyQt6 ≥ 6.6`, `opencv-python ≥ 4.9`, `Pillow ≥ 10.0`,
`numpy ≥ 1.24`. No build step — all interpreted Python.

See the [changelog](../changelog.md) for the version history.
