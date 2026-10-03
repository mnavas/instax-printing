# v0.0.9 — Changelog

## New features

### A4 Instax Sheet (new tool)

- A third tool (**Tools → A4 Instax Sheet**) that packs the **maximum number of
  instax cards onto a landscape A4** for home printing.
- Pick a **format** and fill a grid of crop stations — as many as you like, you
  don't have to fill them all. Capacity per A4:
  - **Instax Mini** — **10** (5×2)
  - **Instax Square** — **8** (4×2)
  - **Instax Wide** — **4** (2×2)
- **Generate A4 sheet** composites the loaded photos into a print-ready A4:
  - **True-size instax cards** (300 DPI, real physical size) with the full white
    instax border (thin top/sides, thick bottom) — **not** reduced.
  - A **light-grey cut line** around every card so they're easy to cut out
    (cards are edge-to-edge, so one cut separates two).
  - The card block is **centred and kept a few mm inside the A4**, so it prints
    centred without the printer clipping the edges.
- **Save** writes a 300-DPI A4 JPEG/PNG/TIFF (`instax_a4[_N]`, last-used folder +
  incremental names); **Print** sends it to a printer. **New sheet** clears it.
- Loaded photos survive a **format change** (crop stations are reused, up to the
  new capacity), like the collage tool.

## New files

| File | Purpose |
|------|---------|
| `a4_sheet.py` | Compose the A4 page — `card_px`, `max_grid`, `max_count`, `make_card`, `build_a4` (no Qt) |
| `a4_page.py` | `A4Page` — the A4 tool UI (format picker + max-grid of crop stations) |

## Changes to existing files

| File | Change |
|------|--------|
| `main_window.py` | `PreviewDialog` gained `title` / `base_name` / `dpi` params (reused for A4); `A4Page` added as a third `QStackedWidget` page with a third **Tools** menu action |
| `README.md`, `docs/user-guide.md`, `docs/architecture.md`, `index.html` | Document the A4 tool |

## Implementation notes

- A4 landscape is 297×210 mm → 3508×2480 px at 300 DPI (`instax_config.mm_to_px`).
- Unlike the collage tool (which renders at each instax printer's *native* pixel
  size), the A4 tool renders at **300 DPI physical size**, so a cut-out card is a
  true-size instax.
- `build_a4` centres a `cols_used × rows_used` block and draws a `cv2.rectangle`
  cut line per card; it raises `ValueError` if given no crops.
- The saved file is exactly A4 with the content inset by a margin — it prints
  centred at true size whether you fit-to-page or print at 100%.
- `a4_sheet.py` is Qt-free, like `composite.py` and `collage.py`.
