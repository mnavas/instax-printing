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
├── instax_config.py   Physical sizes (mm) → pixels @ 300 DPI, and the 3-up layout
├── imaging.py         Unicode-safe image I/O + the crop-transform maths (no Qt)
├── composite.py       Assembles the 4R sheet and draws the cut marks (no Qt)
├── crop_canvas.py     CropCanvas widget — interactive move/zoom/rotate frame
├── main_window.py     CropSlot, PreviewDialog, MainWindow — all the UI
├── run.sh             venv bootstrap + launcher
└── requirements.txt   PyQt6, opencv-python, Pillow, numpy
```

**Dependency direction:** `main_window` → (`crop_canvas`, `composite`, `imaging`,
`instax_config`); `crop_canvas` → (`imaging`, `instax_config`); `composite` →
`instax_config`; `imaging` → (nothing project-local). Nothing lower ever imports
upward.

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

## The UI (`main_window.py`)

Three classes:

### `CropSlot(QWidget)`

One crop station: a `CropCanvas` plus the **Load / ⟲ 90 / ⟳ 90 / Reset** row, the
**Zoom** and **Angle** sliders, and the DPI label. It wires the canvas's `changed`
signal to `_sync_from_canvas`, which pushes the canvas state back into the sliders
(with signals blocked to avoid feedback loops) and updates the DPI readout.

`_last_dir` is a **class attribute**, so the file dialog's remembered folder is
shared across all three slots. `_IMG_EXTS` is listed in both cases so the native
file dialog's case-sensitive globbing doesn't hide `.JPG` photos.

### `PreviewDialog(QDialog)`

Shows the composed sheet (scaled to 900 px wide for display) with **Save… / Print…
/ Close**. Save uses `imaging.imwrite_print` at 300 DPI; Print renders through a
`QPrinter` at `HighResolution`, scaled to fit the page and centred.

### `MainWindow(QMainWindow)`

Holds the three `CropSlot`s and the **Generate 4R sheet** button.
`_update_state()` runs on every change: it enables Generate only when all three
slots are ready and updates the status line (loaded count, low-DPI warnings, or
the green "all ready" message). `_on_generate()` collects the three outputs, calls
`composite.build_4r`, and opens the `PreviewDialog`.

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
