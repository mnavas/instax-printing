# v0.0.9 — Implementation Analysis

## Version Scope

v0.0.9 adds a third tool: **A4 Instax Sheet** — pack the **maximum number of
instax cards onto a landscape A4 page** for home printing, each a real
white-bordered instax card with a **cut line** around it, laid out in a **centred
block kept a few mm inside the A4** so it prints centred without the printer
clipping the edges.

This complements the existing tools:

| Tool | Output | For |
|------|--------|-----|
| 4R Print Sheet | 3 instax mini on a 4R (15×10 cm) | a photo lab |
| Instax Collage | several photos in **one** instax image | an instax printer |
| **A4 Instax Sheet** (new) | **the max instax cards on an A4** | a **home/office printer** + scissors |

**In scope:**
- A4-landscape layout at 300 DPI (physical print size).
- Max-grid packing per instax format (Mini / Square / Wide).
- Real instax cards (white border, thin top/sides, thick bottom).
- A light-grey cut line around every card.
- The card block centred inside a small margin (content < A4 → prints centred).
- A grid of crop stations (one per card); load as many as you like (partial OK).
- Preview + Save (300-DPI A4 image) + Print.

**Deferred:**
- Multiple A4 pages when you have more photos than fit on one.
- Mixing card orientations to squeeze in more.
- Repeating one photo to fill the sheet with a single click (you can still load
  the same photo into each cell by hand).

---

## Page Geometry

A4 landscape is **297 × 210 mm**, i.e. **3508 × 2480 px** at 300 DPI (via the
existing `instax_config.mm_to_px`). Cards are packed in a regular grid, centred,
and kept `EDGE_MARGIN_MM` (4 mm) inside the page edge so the block is always
**smaller than A4** and prints centred without edge-clipping.

Max cards that fit (within A4 − 2·4 mm = 289 × 202 mm usable):

| Format | Card (mm) | Cols × Rows | Cards | Centred margin |
|--------|-----------|-------------|-------|----------------|
| Mini   | 54 × 86   | 5 × 2       | **10** | ~13 mm sides, ~19 mm top/bottom |
| Square | 72 × 86   | 4 × 2       | **8**  | ~4.5 mm sides, ~19 mm top/bottom |
| Wide   | 108 × 86  | 2 × 2       | **4**  | ~40 mm sides, ~19 mm top/bottom |

(The binding case is Square width: four 72 mm cards = 288 mm, leaving ~4.5 mm each
side — still inside the A4, still centred.)

Cards are packed **edge-to-edge** so adjacent cut lines coincide (one cut
separates two cards). If fewer than the maximum are loaded, only that many are
placed (row-major) and the block is sized and centred to the cards actually used.

---

## Compositing (`a4_sheet.py`, pure NumPy)

```
A4_W_MM, A4_H_MM = 297, 210          # landscape; A4_W/A4_H in px @ 300 DPI
EDGE_MARGIN_MM   = 4.0

card_px(fmt)            -> (w, h) px of a full card at 300 DPI
max_grid(fmt)           -> (cols, rows) that fit inside A4 − margins
max_count(fmt)          -> cols * rows
make_card(fmt, crop)    -> one white instax card with the crop in its image area
build_a4(fmt, crops)    -> A4 canvas with up to max_count cards, centred + cut lines
```

- `make_card` places the image-area crop (`mm_to_px(img_w/h_mm)`) inside the card
  at `((card_w−img_w)/2, top_border)` — the same offset model as the 4R tool, but
  derived from the format's millimetres so it works for Mini/Square/Wide.
- `build_a4` centres a `cols_used × rows_used` block on the A4 and draws a
  `cv2.rectangle` cut line (light grey `TRIM_LINE_COLOR`) around each card.
- Everything is at **300 DPI physical size**, so a cut-out card is a true-size
  instax. (This differs from the collage tool, which renders at each instax
  printer's native pixel size — that one feeds a printer, this one feeds paper.)

All Qt-free, like `composite.py` / `collage.py`.

---

## UI (`a4_page.py`)

### `A4Page(QWidget)`

- A **Format** picker (Mini / Square / Wide).
- A `QGridLayout` of **`max_count(fmt)` crop stations** (`CropSlot`, reused),
  arranged `cols × rows`, each cropping to the format's image area.
- Changing the format rebuilds the grid (reusing stations where possible, like
  the collage tool, so loaded photos survive a format change up to the new count).
- A status line (`k / max loaded`) and a **Generate A4 sheet** button, enabled once
  at least one card is loaded (you don't have to fill all of them).
- `_on_generate` collects the filled crops and opens the shared preview dialog.

### Preview / Save / Print

Reuse `main_window.PreviewDialog`, generalised to take a **title**, **save base
name**, and **DPI**. For A4 it shows the composed page with **Save… / Print…**:

- **Save** writes a 300-DPI A4 JPEG/PNG/TIFF (`instax_a4[_N]`), via the shared
  `ui_common.save_image` (last-used folder + incremental naming).
- **Print** sends it through `ui_common.print_image` (fit-to-page, centred). For a
  truly exact size, the saved A4 file can be printed at 100%.

### Menu

`MainWindow`'s **Tools** menu gains a third checkable action, **A4 Instax Sheet**,
added to the existing `QActionGroup`; it switches the `QStackedWidget` to the new
page.

---

## Changes to Existing Modules

| Module | Change |
|--------|--------|
| `main_window.py` | Generalise `PreviewDialog` (title / base name / DPI params); add `A4Page` to the stack and a third **Tools** menu action |
| `instax_config.py` | (none — reuses `mm_to_px`, the formats, and `TRIM_LINE_COLOR`) |

New files: `a4_sheet.py` (compositor), `a4_page.py` (UI).

---

## Decisions

1. **A4-size canvas, content inset by a margin.** Saving a full-A4 image with the
   cards centred inside a margin is the most robust way to "print centred on A4":
   fit-to-page or 100% both land it correctly, and nothing sits in the printer's
   unprintable edge. The *content* is smaller than A4 (the requested behaviour);
   the file is exactly A4 so sizing is unambiguous.
2. **300 DPI physical sizing.** A cut-out card must be a true-size instax, so the
   A4 tool renders at 300 DPI from millimetres — unlike the collage tool's
   printer-native pixels.
3. **Real instax cards + per-card cut rectangle.** Each card has the white instax
   border so the cut-out looks like instax, and a light-grey rectangle marks where
   to cut; edge-to-edge packing means one cut serves both neighbours.
4. **Partial fill allowed.** You can print 1–max cards; the block is sized and
   centred to what's loaded, so you're never forced to fill all ten.
5. **Reuse `CropSlot` + `PreviewDialog`.** Same crop/preview behaviour as the other
   tools; only the compositor and the page wiring are new.
