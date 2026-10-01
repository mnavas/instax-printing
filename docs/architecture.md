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
├── crop_canvas.py     CropCanvas widget — interactive move/zoom/rotate frame (any output size)
├── crop_station.py    CropSlot widget — a CropCanvas + load/rotate/reset + sliders + DPI hint
├── ui_common.py       Shared button styles + save/print helpers (last-used folder, incrementing names)
├── collage_page.py    CollagePage + CollagePreviewDialog — the collage tool UI
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

## Two Tools, One Window

`MainWindow` is a `QMainWindow` with a menu bar and a `QStackedWidget` holding two
pages:

- **`SheetPage`** (index 0) — the original 4R tool: three `CropSlot`s locked to
  the instax-mini output size, a status line, **New sheet** / **Generate 4R
  sheet** buttons, and `PreviewDialog` for save/print.
- **`CollagePage`** (index 1) — the collage tool (see below).

The **Tools** menu holds two checkable, mutually exclusive actions (a
`QActionGroup`) that call `_show_page(index)`; **File → Quit** closes the window.

---

## The Coordinate / Size Model

Everything is anchored to **real millimetres** and rasterised at
`PRINT_DPI = 300`, so the exported file has correct physical proportions.

| Thing | mm | px @ 300 DPI | Constant(s) |
|-------|-----|--------------|-------------|
| 4R sheet (landscape) | 152.4 × 101.6 | 1800 × 1200 | `CANVAS_W`, `CANVAS_H` |
| instax card | 54 × 86 | 638 × 1016 | `CARD_W`, `CARD_H` |
| instax image area | 46 × 62 | 543 × 732 | `INSTAX_W`, `INSTAX_H` |
| top/side border | 4 | ~47 | `TOP_BORDER_PX` |

`mm_to_px(mm)` is the single conversion used everywhere. The image area sits
inside the card centred horizontally, with a 4 mm top/side border; the bottom
border is whatever's left (~20 mm) — the classic instax look.

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
build_4r(crops)                     # crops: exactly three instax-ratio images
  ├─ for each crop:
  │    make_instax_card(crop)        # paste crop into a white 638×1016 card
  │    cv2.resize → card_print_size()
  │    blit onto the 1800×1200 canvas at card_positions()[i]
  └─ _draw_cut_marks(canvas, …)      # 2 vertical cuts + 1 bottom trim
```

- `make_instax_card(crop)` builds one native-size card: a white
  `CARD_H × CARD_W` array with the crop resized into the `INSTAX_W × INSTAX_H`
  image area at `image_offset()`.
- `_draw_cut_marks` draws only the cuts the top-flush, edge-to-edge layout needs:
  two full-height vertical lines at the card boundaries and one horizontal line at
  the card bottom, in light grey (`TRIM_LINE_COLOR`). The left/right/top borders
  are the sheet edges, so nothing is drawn there.

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

### `SheetPage` / `PreviewDialog` — `main_window.py`

`SheetPage` holds the three mini `CropSlot`s, the status line, and the **New
sheet** / **Generate 4R sheet** buttons; `_on_generate` calls `composite.build_4r`
and opens `PreviewDialog`, which shows the sheet (scaled to 900 px) with **Save… /
Print… / Close** via the shared `ui_common` helpers.

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
