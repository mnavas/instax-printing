# v0.0.6 — Implementation Analysis

## Version Scope

v0.0.6 turns instax-printing from a single-purpose app into a **two-tool app
behind a menu bar**, and adds the second tool: **Instax Collage**.

**Tool 1 — 4R Print Sheet** (existing, unchanged behaviour)
Three instax-mini crops laid onto a 4R (15×10 cm) lab print, with cut marks.

**Tool 2 — Instax Collage** (new)
Combine several photos into a **single instax-sized image**. The user picks an
instax **format** (Mini / Square / Wide) and a preset **grid layout** (1, 2, 3, or
2×2), frames a photo in each cell, and exports the result — either as a **bare
image at the instax printer's native resolution** (the printer adds the physical
border) or **with the white instax border drawn on** (for a normal printer or a
true-to-life preview).

**In scope:**
- A menu bar: a **Tools** menu that switches tools, and **File → Quit**.
- Three instax formats defined in real millimetres + printer pixel sizes.
- Preset grid layouts that fill one instax frame.
- Per-cell crop stations (reusing the existing crop widget) at any aspect ratio.
- Collage compositing with a white gutter, image-only or bordered.
- An export preview with a border toggle, plus Save / Print.

**Deferred:**
- Freeform (drag/resize/overlap) collage layouts — this version is preset grids
  only (chosen explicitly over freeform / hybrid).
- A variable/custom number of cells or non-uniform grids.
- Persisting the chosen format/layout or the last-used save folder across
  restarts (still session-only, matching the rest of the app).
- Per-cell aspect lock options, captions, backgrounds / frames beyond plain white.

---

## Architecture Decision: One Window, Two Pages

`MainWindow` becomes a `QMainWindow` with a menu bar and a `QStackedWidget`
holding two page widgets:

```
MainWindow (QMainWindow)
├── menuBar
│     ├── File → Quit
│     └── Tools → ◉ 4R Print Sheet (3 instax mini)   (QActionGroup, exclusive)
│                ○ Instax Collage
└── QStackedWidget
      ├── index 0: SheetPage    (the old MainWindow body, extracted verbatim)
      └── index 1: CollagePage  (new)
```

The two checkable `Tools` actions live in a `QActionGroup` (exclusive) and call
`_show_page(index)`, which flips the stack and updates the window title.

This keeps each tool self-contained and makes adding a third tool later a matter
of one more page + menu action.

---

## Refactor to Support Two Tools

The sheet tool's widgets were hard-wired to the instax-mini ratio and defined
inside `main_window.py`. Three pieces were generalised / extracted so the collage
tool can reuse them without duplication:

### 1. `CropCanvas` — output-size agnostic (`crop_canvas.py`)

Previously the crop output was fixed to module constants
`_OUT_W, _OUT_H = cfg.INSTAX_W, cfg.INSTAX_H`. Now the output size is **instance
state**, set at construction and changeable at runtime:

```python
CropCanvas(out_w=cfg.INSTAX_W, out_h=cfg.INSTAX_H, phys_w_mm=cfg.INSTAX_W_MM)
canvas.set_output_size(out_w, out_h, phys_w_mm)   # e.g. when the layout changes
```

The crop-transform maths in `imaging.py` already took `out_w`/`out_h`, so only the
widget needed to change. `phys_w_mm` (the physical width the output spans) feeds
the DPI readout, which now works for any cell size. `clear()` (added in v0.0.5)
stays.

### 2. `CropSlot` — extracted + generalised (`crop_station.py`)

The crop station (canvas + Load/⟲/⟳/Reset + Zoom/Angle sliders + DPI label) moved
out of `main_window.py` into its own module so both pages import it. Its
constructor now takes the output size, physical width, and an optional button
label:

```python
CropSlot(index, on_change, out_w, out_h, phys_w_mm, label=None)
```

`_last_dir` remains a class attribute, so the file-open dialog's remembered folder
is shared across every slot in **both** tools.

### 3. `ui_common.py` — shared styles + save/print

The three button stylesheets and the Save/Print logic (including the session
last-used folder and incremental naming) were extracted into `ui_common.py`:

```python
STYLE_BTN, STYLE_MINI, STYLE_ACCENT
save_image(parent, bgr, base_name, dpi)   # last-used dir + next_available_path
print_image(parent, bgr, dpi)
```

The sheet's `PreviewDialog` and the new `CollagePreviewDialog` both call these, so
the last-used save folder is shared across tools and there's one copy of the print
code. `next_available_path` itself moved to `imaging.py` (pure, no Qt).

Dependency direction after the refactor (nothing lower imports upward):

```
main_window → collage_page, crop_station, composite, ui_common, instax_config
collage_page → collage, crop_station, ui_common, instax_config
crop_station → crop_canvas, ui_common, instax_config
crop_canvas / composite / collage → imaging, instax_config
ui_common → imaging, instax_config
imaging → (nothing project-local)
```

The pure-NumPy layer (`imaging`, `composite`, `collage`, `instax_config`) stays
Qt-free and unit-testable.

---

## Instax Formats (`instax_config.py`)

A frozen dataclass describes each format in real millimetres plus the **native
image-area pixel resolution of that format's instax printer**, so a collage
exports at exactly the right size to send to the printer.

```python
@dataclass(frozen=True)
class InstaxFormat:
    key: str; label: str
    img_w_mm: float; img_h_mm: float      # image area (the photo content)
    card_w_mm: float; card_h_mm: float    # full card incl. white border
    top_border_mm: float                  # top/side equal; bottom = remainder
    print_px_w: int; print_px_h: int      # instax printer image-area resolution

    dpi_x / dpi_y                          # print_px / (img_mm / 25.4)
    side_border_mm()                       # (card_w - img_w) / 2
    gap_px(gap_mm)                         # white gutter in px
    borders_px() -> (side, top, bottom)    # bottom = card_h - img_h - top
```

| Format | Image mm | Card mm | Printer px (image area) | ~DPI |
|--------|----------|---------|-------------------------|------|
| Mini   | 46 × 62  | 54 × 86 | 600 × 800               | ~331 |
| Square | 62 × 62  | 72 × 86 | 800 × 800               | ~328 |
| Wide   | 99 × 62  | 108 × 86 | 1260 × 840             | ~323 |

`INSTAX_FORMATS` holds the three; `format_by_key()` looks one up. Pixel sizes are
the image-area resolutions reported for Fujifilm's instax printers (SP-2 / Link
for mini, SQ / SP-3 for square, Link Wide for wide) and are the single place to
tweak if a specific printer differs.

---

## Collage Layouts

Preset grids, each filling one instax frame in reading order:

```python
COLLAGE_LAYOUTS = [
    ("1 photo",          1, 1),
    ("2 — stacked",      2, 1),
    ("2 — side by side", 1, 2),
    ("3 — rows",         3, 1),
    ("3 — columns",      1, 3),
    ("4 — grid (2×2)",   2, 2),
]
COLLAGE_GAP_MM = 2.0            # white gutter between + around cells
COLLAGE_BG     = (255, 255, 255)
```

Layouts are format-independent — the same rows×cols grid works for any instax
size; only the cell aspect ratio changes with the format.

---

## Collage Compositing (`collage.py`)

Pure NumPy, no Qt.

```python
grid_cells(rows, cols, width, height, gap)      # (x, y, w, h) per cell
cell_output_size(fmt, rows, cols, gap_mm)        # px (w, h) + physical width mm
build_collage(fmt, rows, cols, crops, with_border, gap_mm, bg) -> np.ndarray
```

- `grid_cells` divides the image area into an even rows×cols grid with a uniform
  `gap` gutter on every side and between cells.
- `cell_output_size` gives the pixel size a cell's crop should render at (so each
  `CropSlot` renders at full export resolution) plus the cell's physical width in
  mm (for the per-cell DPI readout).
- `build_collage` blits each crop into its cell at the printer's native
  resolution. With `with_border=False` it returns the bare image area
  (`print_px_h × print_px_w`). With `with_border=True` it pastes the image area
  inside a full white card sized from `borders_px()` — guaranteeing an exact fit
  (`side + w + side` × `top + h + bottom`) with no rounding overflow. It raises
  `ValueError` unless given exactly `rows*cols` crops.

---

## Collage UI (`collage_page.py`)

### `CollagePage(QWidget)`

- **Format** and **Layout** `QComboBox`es over a `QGridLayout` of `CropSlot`s.
- `_rebuild_cells()` (on either combo change) tears down the old stations and
  builds `rows*cols` fresh ones sized by `collage.cell_output_size`, placed at
  `(r, c)` in the grid.
- `_update_state()` enables **Export collage…** only when every cell is filled,
  mirrors the sheet tool's status line (loaded count, sub-180-DPI warning, green
  "all ready").
- **New collage** clears every cell (confirmation prompt when any are loaded).

### `CollagePreviewDialog(QDialog)`

- Shows the composed collage scaled to fit (720×560, aspect-preserved).
- A **"Add white instax border"** checkbox (default off) re-renders between
  image-only and bordered via `collage.build_collage`.
- **Save…** writes `instax_<key>_collage_<image|border>.jpg` at the format's print
  DPI through `ui_common.save_image`; **Print…** via `ui_common.print_image`.

---

## Data Flow: Collage end-to-end

```
Tools → Instax Collage                          # MainWindow._show_page(1)
  → CollagePage
      choose Format=Square, Layout="4 — grid (2×2)"
        → _rebuild_cells()
             cell_output_size(square, 2, 2) → (cell_w, cell_h, phys_w_mm)
             build 4 × CropSlot(out=cell_w×cell_h, phys_w_mm)
      load + frame a photo in each cell          # CropSlot → CropCanvas crops
      press "Export collage…"
        → crops = [slot.get_output() for slot in cells]   # each cell_w×cell_h
        → CollagePreviewDialog(square, 2, 2, crops)
             _render(): build_collage(..., with_border=False) → 800×800 image
             [user ticks border]
             _render(): build_collage(..., with_border=True)  → 930×1110 card
             Save… → ui_common.save_image(bgr, "instax_square_collage_border",
                                           dpi=round(fmt.dpi_x))
```

---

## Changes to Existing Modules

| Module | Change |
|--------|--------|
| `instax_config.py` | Added `InstaxFormat` dataclass, `INSTAX_FORMATS`, `format_by_key`, `COLLAGE_LAYOUTS`, `COLLAGE_GAP_MM`, `COLLAGE_BG` |
| `imaging.py` | Added `next_available_path` (moved from `main_window.py`); added `os` import |
| `crop_canvas.py` | `CropCanvas` now takes `out_w`/`out_h`/`phys_w_mm`; added `set_output_size`; min size 300×380 → 150×150; module `_OUT_*` constants → instance state |
| `main_window.py` | Extracted the sheet UI into `SheetPage`; `PreviewDialog` now uses `ui_common` helpers; `MainWindow` is now a menu + `QStackedWidget` host; removed local styles and `_next_available_path` |

New files: `collage.py`, `collage_page.py`, `crop_station.py`, `ui_common.py`.

---

## Error Cases

| Situation | Behaviour |
|-----------|-----------|
| Not every collage cell filled | **Export** disabled; status shows `n / total photos loaded` |
| A cell's crop is below 180 DPI | Cell DPI label red + `⚠ low-res`; status names the cell(s) |
| `build_collage` given ≠ `rows*cols` crops | Raises `ValueError` (guards a UI bug) |
| Card rounding would overflow the image area | Card is sized from borders (`side+w+side`, `top+h+bottom`), so the paste always fits |
| Switching format/layout with photos loaded | Cells are rebuilt and cleared (expected — the grid shape changes) |
| Save/Print with an unreadable path | `imaging.imwrite_print` returns False → "Save failed" dialog |

---

## Decisions

1. **Preset grids, not freeform.** Explicit product choice. Preset grids are fast
   to build, predictable to use, and reuse the existing crop station per cell with
   no new interaction model. Freeform/hybrid deferred.
2. **All three formats from day one.** Mini / Square / Wide differ only by numbers
   in `INSTAX_FORMATS`, so supporting all three costs almost nothing.
3. **Export at the printer's native resolution.** The image-only output is exactly
   the instax printer's image-area pixel size, so no resampling happens on the
   device; the physical border comes from the film itself.
4. **Border as a preview toggle, not two buttons.** One preview with a checkbox
   re-renders instantly between image-only and bordered, so the user sees exactly
   what each option produces before saving.
5. **Reuse, don't fork, the crop widget.** Generalising `CropCanvas`'s output size
   (rather than writing a second crop widget) keeps one code path for the crop
   maths, DPI readout, and interaction.
6. **Shared save/print + last-used folder.** Extracted to `ui_common` so both
   tools behave identically and the folder is remembered across tools in a
   session.
7. **Session-only state.** No config file yet; format/layout and last-save-dir
   reset on restart, consistent with the rest of the app.
