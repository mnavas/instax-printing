# v0.0.6 — Changelog

## New features

### Main menu

- The window now has a **menu bar**:
  - **File → Quit** (Ctrl+Q)
  - **Tools** — two checkable, mutually exclusive actions that switch tools:
    **4R Print Sheet (3 instax mini)** and **Instax Collage**
- The two tools live in a `QStackedWidget`; switching updates the window title.

### Instax Collage (new tool)

- Combine several photos into a **single instax-sized image**.
- **Format** picker — Instax **Mini** (46×62 mm), **Square** (62×62 mm), or
  **Wide** (99×62 mm). Each exports at its instax printer's native image-area
  resolution: 600×800, 800×800, 1260×840.
- **Layout** picker — preset grids that fill one frame: `1 photo`, `2 — stacked`,
  `2 — side by side`, `3 — rows`, `3 — columns`, `4 — grid (2×2)`.
- Each cell is a full crop station (Load / ⟲ 90 / ⟳ 90 / Reset, Zoom + Angle
  sliders, live DPI readout) locked to that cell's shape. A thin white gutter
  (2 mm) separates the cells.
- **Export preview with a border toggle:**
  - **Image only** (default) — the bare image area at the printer's native
    resolution, to send to an instax printer (the film provides the border).
  - **Add white instax border** — the collage inside a full instax card (thin
    top/sides, thick bottom), for a normal printer or a true-to-life preview.
- **Save…** writes `instax_<format>_collage_<image|border>.jpg/png/tiff` with the
  instax print DPI embedded, reusing the last-used folder and incremental naming.
  **Print…** sends it to a printer. **New collage** clears every cell.

## Internal changes

### Refactor to support two tools (no behaviour change to the sheet tool)

- **`CropCanvas` is now output-size agnostic.** It takes `out_w` / `out_h` /
  `phys_w_mm` and gains `set_output_size(...)`, so the same crop widget drives both
  the instax-mini sheet crop and arbitrary-aspect collage cells. Minimum widget
  size lowered (300×380 → 150×150).
- **`CropSlot` extracted to `crop_station.py`** and generalised (takes the output
  size + an optional button label). Shared by both tools; the file-dialog's
  remembered folder (`_last_dir`) is shared across every slot in both tools.
- **`ui_common.py` (new)** — shared button styles (`STYLE_BTN/MINI/ACCENT`) and
  `save_image` / `print_image` helpers, so both tools share one save/print code
  path and one session last-used folder.
- **`next_available_path` moved to `imaging.py`** (pure, no Qt).

### New files

| File | Purpose |
|------|---------|
| `collage.py` | `grid_cells`, `cell_output_size`, `build_collage` — collage assembly (no Qt) |
| `collage_page.py` | `CollagePage` + `CollagePreviewDialog` — the collage tool UI |
| `crop_station.py` | `CropSlot` — the shared crop station widget |
| `ui_common.py` | Shared styles + save/print helpers |

## Changes to existing files

| File | Change |
|------|--------|
| `instax_config.py` | Added `InstaxFormat` dataclass, `INSTAX_FORMATS`, `format_by_key`, `COLLAGE_LAYOUTS`, `COLLAGE_GAP_MM`, `COLLAGE_BG` |
| `imaging.py` | Added `next_available_path` (+ `os` import) |
| `crop_canvas.py` | Parameterised output size; added `set_output_size`; instance state instead of `_OUT_*` constants |
| `main_window.py` | Extracted the sheet UI into `SheetPage`; `PreviewDialog` uses `ui_common`; `MainWindow` is now a menu bar + `QStackedWidget` host; removed local styles and `_next_available_path` |
| `README.md` | Two-tool intro + Instax Collage section + updated code layout |
| `docs/user-guide.md` | Added "Two Tools (the menu)" and "Instax Collage" sections |
| `docs/architecture.md` | Updated module map; added "Two Tools, One Window", instax formats + collage sections |
| `index.html` | Added an Instax Collage feature card |

## Implementation notes

- Instax printer pixel sizes are the commonly-cited image-area resolutions
  (SP-2 / Link = 600×800, SQ / SP-3 = 800×800, Link Wide = 1260×840) and live in
  `INSTAX_FORMATS` — the single place to adjust for a specific printer.
- `build_collage` sizes the bordered card from `borders_px()`
  (`side + w + side` × `top + h + bottom`) so the image-area paste always fits
  exactly, with no rounding overflow.
- The pure-NumPy layer (`imaging`, `composite`, `collage`, `instax_config`) stays
  free of Qt and is exercised headless with `QT_QPA_PLATFORM=offscreen`.
- State is session-only (format/layout and last-used save folder reset on
  restart), consistent with the rest of the app.
