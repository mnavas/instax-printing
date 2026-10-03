# v0.0.9 — Implementation Plan

## Prerequisites

- v0.0.8 working (instax theme, collage tool, sheet tool)
- No new pip packages
- Decisions settled (see analysis): A4 landscape, 300 DPI, max grid per format,
  real instax cards, per-card cut line, centred block inside a 4 mm margin

---

## Phase 1 — Compositor (`a4_sheet.py`, no Qt)

### Step 1 — Geometry helpers

```python
A4_W_MM, A4_H_MM = 297.0, 210.0
A4_W, A4_H = cfg.mm_to_px(A4_W_MM), cfg.mm_to_px(A4_H_MM)   # 3508 x 2480
EDGE_MARGIN_MM = 4.0

def card_px(fmt): ...            # (w, h) px of a full card @ 300 DPI
def max_grid(fmt): ...           # (cols, rows) inside A4 - 2*margin
def max_count(fmt): ...          # cols * rows
```

### Step 2 — Card + page

```python
def make_card(fmt, crop):        # white card, crop in the image area (300 DPI)
def build_a4(fmt, crops):        # up to max_count cards, centred block + cut lines
```

- `make_card` resizes the crop into `mm_to_px(img_w/h_mm)` at
  `((card_w-img_w)//2, mm_to_px(top_border_mm))`.
- `build_a4` centres a `cols_used × rows_used` block, blits each card, and draws a
  light-grey `cv2.rectangle` cut line around it. Raises `ValueError` if no crops.

**Checkpoint:** build an A4 from dummy crops for each format; assert the canvas is
3508×2480, the right card count is placed, and the block is centred and inside the
margin. Render one and eyeball the borders + cut lines.

---

## Phase 2 — Generalise the preview dialog (`main_window.py`)

### Step 3 — `PreviewDialog` params

```python
class PreviewDialog(QDialog):
    def __init__(self, canvas_bgr, parent=None,
                 title="4R print preview — 15×10 cm",
                 base_name="instax_4r", dpi=cfg.PRINT_DPI): ...
```

`_save`/`_print` use `self._base` / `self._dpi`. The existing 4R call site keeps
working on the defaults.

---

## Phase 3 — A4 page (`a4_page.py`)

### Step 4 — `A4Page(QWidget)`

- **Format** combo (Mini / Square / Wide).
- `QGridLayout` of `max_count(fmt)` `CropSlot`s (out size = image area px), rebuilt
  on format change — **reuse stations** so loaded photos survive (same pattern as
  the collage page: grow/shrink list, re-size in place).
- Status line `k / max loaded`; **Generate A4 sheet** enabled when `k ≥ 1`.
- `_on_generate`: gather the filled crops (in order) → `a4_sheet.build_a4` →
  `PreviewDialog(sheet, self, title="A4 instax sheet — 297×210 mm",
  base_name="instax_a4", dpi=300)`.

**Checkpoint:** construct the page headless; switch formats; confirm the grid cell
count matches `max_count`; load a few and generate.

---

## Phase 4 — Wire into the window (`main_window.py`)

### Step 5 — Menu + stack

- Add `A4Page` as a third `QStackedWidget` page.
- Add a third checkable **Tools** action, **A4 Instax Sheet**, to the
  `QActionGroup`; `_show_page(2)` switches to it and sets the title.

**Checkpoint:** launch; switch between all three tools; generate an A4 and
Save/Print.

---

## Phase 5 — Verify + document

### Step 6 — Headless smoke test

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -c "..."
```

- `max_count`: Mini 10, Square 8, Wide 4.
- `build_a4` for each format: shape 2480×3508, k cards placed, centred.
- Page rebuilds correctly per format; photos survive a format change.
- Render an A4 (mini, a few cards) and inspect borders + cut lines.
- `py_compile` all modules.

### Step 7 — Docs

- `README.md` — add the A4 tool to the two-tool intro (now three) + a short section.
- `docs/user-guide.md` — "A4 Instax Sheet" section.
- `docs/architecture.md` — module map + `a4_sheet.py` / `a4_page.py` + geometry.
- `index.html` — a feature card.
- `changelog.md` — v0.0.9 entry.
- `docs/versioning/v0.0.9/changelog.md` — detailed per-version changelog.

---

## Deliverables

| File | Status |
|------|--------|
| `a4_sheet.py` (new) | pending |
| `a4_page.py` (new) | pending |
| `main_window.py` (PreviewDialog params, A4 page + menu) | pending |
| `README.md`, `docs/user-guide.md`, `docs/architecture.md`, `index.html` | pending |
| `changelog.md` + `docs/versioning/v0.0.9/changelog.md` | pending |
