# v0.0.6 — Implementation Plan

## Prerequisites

- v0.0.5 fully working (New sheet, last-used save folder, incremental names)
- No new pip packages — PyQt6 / OpenCV / Pillow / NumPy already cover everything
- Decisions settled: **preset grid layouts** (not freeform), **Mini + Square +
  Wide** formats

---

## Phase 0 — Refactor for reuse (no behaviour change)

Make the sheet tool's pieces reusable so the collage tool can share them. The app
must behave exactly as v0.0.5 after this phase.

### Step 1 — Generalise `CropCanvas` (`crop_canvas.py`)

- Replace module constants `_OUT_W, _OUT_H` with instance state.
- Constructor: `CropCanvas(out_w=cfg.INSTAX_W, out_h=cfg.INSTAX_H, phys_w_mm=cfg.INSTAX_W_MM)`.
- Add `set_output_size(out_w, out_h, phys_w_mm=None)` — updates and re-clamps.
- Route `scale()`, `get_output()`, `source_dpi()`, `_apply()`, `paintEvent()` and
  `clamp_center`/`crop_quad_src` calls through `self._out_w/_out_h/_phys_w_mm`.
- Lower the minimum widget size (300×380 → 150×150) so 2×2 cells fit.

**Checkpoint:** sheet tool still works and crops are identical (default output =
instax mini).

### Step 2 — Extract `CropSlot` → `crop_station.py`

- Move `CropSlot` out of `main_window.py`.
- Constructor gains `out_w, out_h, phys_w_mm, label=None`; passes them to its
  `CropCanvas`; Load button text = `label or f"Load #{i+1}"`.
- Add `set_output_size(...)` delegating to the canvas.
- Keep `_last_dir` as a class attribute (shared folder memory).

### Step 3 — Extract shared styles + save/print → `ui_common.py`

- Move `STYLE_BTN / STYLE_MINI / STYLE_ACCENT`.
- `save_image(parent, bgr, base_name, dpi)` — last-used dir + `next_available_path`.
- `print_image(parent, bgr, dpi)` — the `QPrinter` render.
- Move `_next_available_path` → `imaging.next_available_path` (pure, no Qt).
- Point the sheet `PreviewDialog` at `ui_common`.

**Checkpoint:** `py_compile` all modules; sheet Save/Print/incremental-naming
unchanged.

---

## Phase 1 — Instax formats + layouts (`instax_config.py`)

### Step 4 — `InstaxFormat` dataclass + `INSTAX_FORMATS`

```python
@dataclass(frozen=True)
class InstaxFormat:
    key, label
    img_w_mm, img_h_mm
    card_w_mm, card_h_mm
    top_border_mm
    print_px_w, print_px_h
    # dpi_x / dpi_y, side_border_mm(), gap_px(mm), borders_px() -> (side, top, bottom)
```

Values:

| key | img mm | card mm | top | printer px |
|-----|--------|---------|-----|------------|
| mini   | 46×62 | 54×86  | 4.0 | 600×800   |
| square | 62×62 | 72×86  | 5.0 | 800×800   |
| wide   | 99×62 | 108×86 | 4.0 | 1260×840  |

Add `format_by_key(key)`, `COLLAGE_LAYOUTS`, `COLLAGE_GAP_MM`, `COLLAGE_BG`.

**Checkpoint:** print `borders_px()` and `dpi_x` for each format; sanity-check the
card sizes are plausible (side/top small, bottom thick).

---

## Phase 2 — Collage compositing (`collage.py`, no Qt)

### Step 5 — Grid + build

```python
def grid_cells(rows, cols, width, height, gap): ...        # (x, y, w, h) per cell
def cell_output_size(fmt, rows, cols, gap_mm=...): ...      # (w, h, phys_w_mm)
def build_collage(fmt, rows, cols, crops, with_border,
                  gap_mm=..., bg=...): ...                  # image area or card
```

- Even rows×cols grid with a uniform gutter on every side and between cells.
- `build_collage` blits each crop (resized to its cell) at the printer's native
  resolution; `with_border=True` pastes the image area inside a white card sized
  from `borders_px()` (exact fit, no overflow).
- Raise `ValueError` unless `len(crops) == rows*cols`.

**Checkpoint:** build a collage from dummy arrays for every format × layout;
assert image area == `(print_px_h, print_px_w)` and the bordered card is strictly
larger.

---

## Phase 3 — Collage UI (`collage_page.py`)

### Step 6 — `CollagePage(QWidget)`

- **Format** + **Layout** combo boxes (populate first, then connect
  `currentIndexChanged` → `_rebuild_cells` to avoid a premature signal).
- `_rebuild_cells()`: delete old slots; create `rows*cols` `CropSlot`s sized by
  `cell_output_size`; add to a `QGridLayout` at `(r, c)`.
- `_update_state()`: enable **Export collage…** only when all cells ready; status
  line with sub-180-DPI warning.
- **New collage** button: clear all cells (confirm when any loaded).
- `_on_export()`: gather crops → open `CollagePreviewDialog`.

### Step 7 — `CollagePreviewDialog(QDialog)`

- Image label (scaled to fit 720×560), a **"Add white instax border"** checkbox
  (default off), Save / Print / Close.
- `_render()` builds via `collage.build_collage(..., self._border.isChecked())`
  and updates the pixmap; the checkbox's `toggled` re-renders.
- Save/Print via `ui_common`, DPI = `round(fmt.dpi_x)`, base name
  `instax_<key>_collage_<image|border>`.

**Checkpoint:** construct the dialog headless; toggle the checkbox; confirm the
stored `bgr` shape flips between image area and card.

---

## Phase 4 — Menu + page stack (`main_window.py`)

### Step 8 — `SheetPage`

- Extract the v0.0.5 `MainWindow` body (three mini `CropSlot`s, status, New sheet
  / Generate, `_update_state`, `_on_new_sheet`, `_on_generate`) into a `QWidget`.

### Step 9 — `MainWindow`

- `QMainWindow` with a dark-styled menu bar + `QStackedWidget(SheetPage,
  CollagePage)`.
- **File → Quit** (Ctrl+Q).
- **Tools** menu: two checkable actions in an exclusive `QActionGroup` →
  `_show_page(0|1)`, which also updates the window title.

**Checkpoint:** launch; switch tools via the menu; run both tools end-to-end.

---

## Phase 5 — Verify + document

### Step 10 — Headless smoke test

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -c "..."
```

- MainWindow constructs; page switching works.
- Every format × layout rebuilds the right cell count and builds a collage.
- Both preview dialogs build; the collage border toggle re-renders.
- `py_compile` all modules; grep for stale symbols.

### Step 11 — Docs

- `README.md` — two-tool intro + Instax Collage section + updated code layout.
- `docs/user-guide.md` — "Two Tools (the menu)" note + "Instax Collage" section.
- `docs/architecture.md` — module map, "Two Tools, One Window", formats + collage.
- `index.html` — a collage feature card.
- `changelog.md` — v0.0.6 entry.
- `docs/versioning/v0.0.6/{analysis,plan,changelog}.md`.

---

## Deliverables

| File | Status |
|------|--------|
| `crop_canvas.py` (generalised) | pending |
| `crop_station.py` (new) | pending |
| `ui_common.py` (new) | pending |
| `imaging.py` (`next_available_path`) | pending |
| `instax_config.py` (formats + layouts) | pending |
| `collage.py` (new) | pending |
| `collage_page.py` (new) | pending |
| `main_window.py` (menu + stack + SheetPage) | pending |
| `README.md`, `docs/user-guide.md`, `docs/architecture.md`, `index.html` | pending |
| `changelog.md` + `docs/versioning/v0.0.6/*` | pending |
